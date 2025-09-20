import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import time
import argparse

KEYWORDS = ['дизайн', 'фото', 'web', 'python']
SEARCH_MODE = 'any'  # 'any' - найти хотя бы одно ключевое слово, 'all' - найти все ключевые слова

def get_article_full_text(article_url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(article_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        article_content = soup.find('div', class_='post__text')
        
        if article_content:
            for script in article_content(["script", "style"]):
                script.decompose()
            
            full_text = article_content.get_text(strip=True)
            return full_text
        else:
            return ""
            
    except requests.RequestException as e:
        print(f"Ошибка при получении статьи {article_url}: {e}")
        return ""

def parse_habr_articles(full_text_analysis=False):
    url = 'https://habr.com/ru/all/'
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = soup.find_all('article', class_='post')
        
        matching_articles = []
        
        if full_text_analysis:
            print(f"Найдено {len(articles)} статей для анализа...")
        
        for i, article in enumerate(articles, 1):
            try:
                if full_text_analysis:
                    print(f"Обрабатываю статью {i}/{len(articles)}...")
                
                title_elem = article.find('h2', class_='post__title')
                if not title_elem:
                    continue
                
                title_link = title_elem.find('a')
                if not title_link:
                    continue
                    
                title = title_link.get_text(strip=True)
                article_url = urljoin(url, title_link.get('href'))
                
                date_elem = article.find('time', class_='post__time')
                date = date_elem.get_text(strip=True) if date_elem else 'Дата не найдена'
                
                preview_elem = article.find('div', class_='post__text')
                preview_text = preview_elem.get_text(strip=True) if preview_elem else ''
                
                search_text = f"{title} {preview_text}".lower()
                
                if full_text_analysis:
                    print(f"  Загружаю полный текст статьи...")
                    full_text = get_article_full_text(article_url)
                    search_text = f"{search_text} {full_text}".lower()
                    time.sleep(1)
                else:
                    full_text = ""
                
                found_keywords = []
                keyword_positions = {}
                
                for keyword in KEYWORDS:
                    keyword_lower = keyword.lower()
                    positions = []
                    start = 0
                    
                    while True:
                        pos = search_text.find(keyword_lower, start)
                        if pos == -1:
                            break
                        positions.append(pos)
                        start = pos + 1
                    
                    if positions:
                        found_keywords.append(keyword)
                        keyword_positions[keyword] = len(positions)
                
                should_include = False
                if SEARCH_MODE == 'any':
                    should_include = len(found_keywords) > 0
                elif SEARCH_MODE == 'all':
                    should_include = len(found_keywords) == len(KEYWORDS)
                
                if should_include:
                    article_data = {
                        'date': date,
                        'title': title,
                        'url': article_url,
                        'keywords': found_keywords,
                        'keyword_counts': keyword_positions
                    }
                    
                    if full_text_analysis:
                        article_data['has_full_text'] = bool(full_text)
                    
                    matching_articles.append(article_data)
                    
            except Exception as e:
                print(f"Ошибка при обработке статьи: {e}")
                continue
        
        return matching_articles
        
    except requests.RequestException as e:
        print(f"Ошибка при получении страницы: {e}")
        return []

def print_results(articles, full_text_analysis=False):
    if not articles:
        print("Статьи с указанными ключевыми словами не найдены.")
        return
    
    if full_text_analysis:
        print(f"\nНайдено {len(articles)} статей с ключевыми словами: {', '.join(KEYWORDS)}")
        print("=" * 100)
        
        for article in articles:
            print(f"Дата: {article['date']}")
            print(f"Заголовок: {article['title']}")
            print(f"Ссылка: {article['url']}")
            print(f"Найденные ключевые слова: {', '.join(article['keywords'])}")
            
            if article['keyword_counts']:
                print("Количество вхождений:")
                for keyword, count in article['keyword_counts'].items():
                    print(f"  - '{keyword}': {count} раз")
            
            print(f"Полный текст статьи: {'Доступен' if article['has_full_text'] else 'Не доступен'}")
            print("-" * 100)
    else:
        print(f"Найдено {len(articles)} статей с ключевыми словами: {', '.join(KEYWORDS)}")
        print("-" * 80)
        
        for article in articles:
            print(f"{article['date']} – {article['title']} – {article['url']}")
            print(f"Найденные ключевые слова: {', '.join(article['keywords'])}")
            print("-" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Парсер статей с Habr.com')
    parser.add_argument('--full', action='store_true', 
                       help='Анализировать полный текст статей (медленнее, но точнее)')
    parser.add_argument('--keywords', nargs='+', 
                       help='Ключевые слова для поиска (по умолчанию: дизайн, фото, web, python)')
    parser.add_argument('--mode', choices=['any', 'all'], default='any',
                       help='Режим поиска: any - найти хотя бы одно ключевое слово, all - найти все ключевые слова')
    
    args = parser.parse_args()
    
    if args.keywords:
        KEYWORDS = args.keywords
    
    SEARCH_MODE = args.mode
    
    if args.full:
        print("Расширенный парсинг статей с Habr.com...")
        print("Анализ включает полный текст статей")
    else:
        print("Парсинг статей с Habr.com...")
        print("Анализ только preview-информации")
    
    print(f"Ключевые слова для поиска: {', '.join(KEYWORDS)}")
    print(f"Режим поиска: {SEARCH_MODE} (найти {'хотя бы одно' if SEARCH_MODE == 'any' else 'все'} ключевое слово)")
    print()
    
    articles = parse_habr_articles(full_text_analysis=args.full)
    print_results(articles, full_text_analysis=args.full)