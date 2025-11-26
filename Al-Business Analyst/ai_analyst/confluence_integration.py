"""
Модуль для интеграции с Confluence API
Позволяет автоматически создавать страницы с бизнес-требованиями
"""
import json
import base64
from typing import Dict, Optional
import requests

# Конфигурация Confluence (можно вынести в config.py)
CONFLUENCE_URL = "https://your-confluence-instance.atlassian.net"
CONFLUENCE_USERNAME = "your-email@example.com"
CONFLUENCE_API_TOKEN = "your-api-token"
CONFLUENCE_SPACE_KEY = "YOUR_SPACE_KEY"

def create_confluence_page(project_data: Dict, space_key: Optional[str] = None) -> Dict:
    """
    Создает страницу в Confluence с бизнес-требованиями
    
    Args:
        project_data: Данные проекта из AI-анализа
        space_key: Ключ пространства Confluence
    
    Returns:
        Dict с результатом создания страницы
    """
    if space_key is None:
        space_key = CONFLUENCE_SPACE_KEY
    
    # Формируем контент страницы в формате Confluence Storage Format
    content = format_confluence_content(project_data)
    
    # Заголовок страницы
    title = f"Бизнес-требования: {project_data.get('project_name', 'Проект')}"
    
    # Подготовка данных для API
    page_data = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "body": {
            "storage": {
                "value": content,
                "representation": "storage"
            }
        }
    }
    
    # В реальной реализации здесь был бы запрос к Confluence API
    # Для демонстрации возвращаем заглушку
    return {
        "success": True,
        "message": "Страница успешно создана (демо-режим)",
        "page_url": f"{CONFLUENCE_URL}/spaces/{space_key}/pages/{123456}/",
        "page_id": "123456",
        "title": title,
        "note": "Для реальной интеграции необходимо настроить API токен в config.py"
    }

def format_confluence_content(project_data: Dict) -> str:
    """
    Форматирует данные проекта в формат Confluence Storage Format
    """
    content = f"<h1>{project_data.get('project_name', 'Проект')}</h1>\n\n"
    
    # Цель
    if project_data.get('goal'):
        content += f"<h2>Цель проекта</h2>\n<p>{project_data.get('goal')}</p>\n\n"
    
    # Scope
    if project_data.get('scope'):
        content += "<h2>Scope проекта</h2>\n"
        if project_data['scope'].get('in_scope'):
            content += "<h3>Входит в scope:</h3>\n<ul>\n"
            for item in project_data['scope']['in_scope']:
                content += f"<li>{item}</li>\n"
            content += "</ul>\n"
        if project_data['scope'].get('out_scope'):
            content += "<h3>Не входит в scope:</h3>\n<ul>\n"
            for item in project_data['scope']['out_scope']:
                content += f"<li>{item}</li>\n"
            content += "</ul>\n"
    
    # Участники
    if project_data.get('actors'):
        content += "<h2>Участники (Actors)</h2>\n<ul>\n"
        for actor in project_data['actors']:
            if isinstance(actor, dict):
                content += f"<li><strong>{actor.get('role')}</strong>: {actor.get('description', '')}</li>\n"
            else:
                content += f"<li>{actor}</li>\n"
        content += "</ul>\n\n"
    
    # Триггер
    if project_data.get('trigger'):
        content += f"<h2>Триггер процесса</h2>\n<p>{project_data.get('trigger')}</p>\n\n"
    
    # Ожидаемый результат
    if project_data.get('expected_result'):
        content += f"<h2>Ожидаемый результат</h2>\n<p>{project_data.get('expected_result')}</p>\n\n"
    
    # Бизнес-правила
    if project_data.get('business_rules'):
        content += "<h2>Бизнес-правила</h2>\n<ol>\n"
        for rule in project_data['business_rules']:
            content += f"<li>{rule}</li>\n"
        content += "</ol>\n\n"
    
    # KPI
    if project_data.get('kpi'):
        content += "<h2>KPI и метрики</h2>\n<table>\n<tr><th>Метрика</th><th>Целевое значение</th><th>Описание</th></tr>\n"
        for kpi in project_data['kpi']:
            if isinstance(kpi, dict):
                content += f"<tr><td>{kpi.get('metric', '')}</td><td>{kpi.get('target', '')}</td><td>{kpi.get('description', '')}</td></tr>\n"
        content += "</table>\n\n"
    
    # Требования
    if project_data.get('requirements'):
        content += "<h2>Функциональные требования</h2>\n<ol>\n"
        for req in project_data['requirements']:
            content += f"<li>{req}</li>\n"
        content += "</ol>\n\n"
    
    # Use Cases
    if project_data.get('use_cases'):
        content += "<h2>Use Cases</h2>\n"
        for uc in project_data['use_cases']:
            if isinstance(uc, dict):
                content += f"<h3>{uc.get('id', '')} - {uc.get('title', '')}</h3>\n"
                content += f"<p><strong>Actor:</strong> {uc.get('actor', '')}</p>\n"
                content += f"<p><strong>Precondition:</strong> {uc.get('precondition', '')}</p>\n"
                content += "<p><strong>Main Flow:</strong></p>\n<ol>\n"
                for step in uc.get('main_flow', []):
                    content += f"<li>{step}</li>\n"
                content += "</ol>\n"
                content += f"<p><strong>Postcondition:</strong> {uc.get('postcondition', '')}</p>\n\n"
    
    # User Stories
    if project_data.get('user_stories'):
        content += "<h2>User Stories</h2>\n"
        for us in project_data['user_stories']:
            if isinstance(us, dict):
                content += f"<h3>{us.get('id', '')}</h3>\n"
                content += f"<p><strong>As</strong> {us.get('as', '')} <strong>I want</strong> {us.get('i_want', '')} <strong>so that</strong> {us.get('so_that', '')}</p>\n"
                if us.get('acceptance_criteria'):
                    content += "<p><strong>Acceptance Criteria:</strong></p>\n<ul>\n"
                    for criteria in us.get('acceptance_criteria', []):
                        content += f"<li>{criteria}</li>\n"
                    content += "</ul>\n\n"
    
    # Диаграмма
    if project_data.get('mermaid_code'):
        content += "<h2>Диаграмма процесса</h2>\n"
        content += f"<p><img src=\"{generate_diagram_link(project_data['mermaid_code'])}\" alt=\"Sequence Diagram\" /></p>\n"
    
    return content

def generate_diagram_link(mermaid_code: str) -> str:
    """Превращает код диаграммы в картинку через сервис mermaid.ink"""
    graphbytes = mermaid_code.encode("utf8")
    base64_bytes = base64.b64encode(graphbytes)
    base64_string = base64_bytes.decode("ascii")
    return "https://mermaid.ink/img/" + base64_string

def test_confluence_connection() -> Dict:
    """Тестирует подключение к Confluence API"""
    # В реальной реализации здесь был бы запрос к /rest/api/space
    return {
        "connected": False,
        "message": "Интеграция с Confluence в демо-режиме. Для реального использования настройте API токен.",
        "note": "Для настройки добавьте CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN в config.py"
    }

