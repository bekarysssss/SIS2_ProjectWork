import os
import json
import time
import requests
from typing import List, Dict, Any

TMDB_BASE_URL = "https://api.themoviedb.org/3"
DEFAULT_RAW_DATA_PATH = os.path.join("data", "raw_data.json")

def fetch_movie_ids(api_key: str, target_count: int = 250) -> List[int]:
    """
    Получает список уникальных ID фильмов через эндпоинт discover/movie.
    """
    movie_ids = []
    page = 1
    
    print(f"[API Client] Начинаем сбор ID фильмов (цель: {target_count} шт.)...")
    
    while len(movie_ids) < target_count:
        url = f"{TMDB_BASE_URL}/discover/movie"
        params = {
            "api_key": api_key,
            "language": "en-US",
            "sort_by": "popularity.desc",
            "include_adult": "false",
            "page": page
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results", [])
            if not results:
                print("[API Client] Больше нет доступных страниц.")
                break
                
            for movie in results:
                if movie["id"] not in movie_ids:
                    movie_ids.append(movie["id"])
                    if len(movie_ids) >= target_count:
                        break
            
            page += 1
            time.sleep(0.2)  
            
        except requests.exceptions.RequestException as e:
            print(f"[API Client] Ошибка при запросе страницы {page}: {e}")
            break
            
    print(f"[API Client] Успешно собрано ID фильмов: {len(movie_ids)}")
    return movie_ids

def fetch_movie_details(api_key: str, movie_ids: List[int]) -> List[Dict[str, Any]]:
    """
    Выгружает полные детали по каждому фильму.
    """
    raw_movies = []
    print(f"[API Client] Загрузка детальных данных для {len(movie_ids)} фильмов...")
    
    for idx, m_id in enumerate(movie_ids, 1):
        url = f"{TMDB_BASE_URL}/movie/{m_id}"
        params = {"api_key": api_key, "language": "en-US"}
        
        try:
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                raw_movies.append(res.json())
            else:
                print(f"[API Client] Ошибка HTTP {res.status_code} для ID {m_id}")
        except requests.exceptions.RequestException as e:
            print(f"[API Client] Сбой подключения для ID {m_id}: {e}")
            
        if idx % 50 == 0 or idx == len(movie_ids):
            print(f"[API Client] Обработано: {idx}/{len(movie_ids)}")
            
        time.sleep(0.1)
        
    return raw_movies

def save_raw_data(data: List[Dict[str, Any]], filepath: str = DEFAULT_RAW_DATA_PATH) -> None:
    """
    Сохраняет сырые данные в JSON перед любой очисткой.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"[API Client] Исходные сырые данные ({len(data)} записей) сохранены в: {filepath}")

def run_data_collection(api_key: str, target_count: int = 250) -> List[Dict[str, Any]]:
    """
    Основная функция запуска первого этапа.
    """
    movie_ids = fetch_movie_ids(api_key, target_count=target_count)
    raw_data = fetch_movie_details(api_key, movie_ids)
    
    if len(raw_data) < 200:
        raise ValueError(f"Собрано недостаточно данных: {len(raw_data)} < 200")
        
    save_raw_data(raw_data)
    return raw_data

if __name__ == "__main__":
    API_KEY = os.getenv("TMDB_API_KEY", "YOUR_TMDB_API_KEY")
    if API_KEY == "YOUR_TMDB_API_KEY":
        print("Внимание: Укажите ваш TMDB_API_KEY или установите переменную окружения.")
    else:
        run_data_collection(api_key=API_KEY, target_count=220)
