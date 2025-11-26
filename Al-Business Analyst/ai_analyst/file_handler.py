"""
Модуль для работы с файлами: сохранение, обработка, генерация документов
"""
import os
import json
from typing import Optional, Dict
from datetime import datetime
import tempfile

# Папка для временных файлов
TEMP_DIR = "temp_files"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def save_file(file_path: str, user_id: int, file_type: str = "document") -> Dict:
    """Сохраняет файл во временную папку"""
    try:
        # Создаем уникальное имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = os.path.splitext(file_path)[1] if file_path else ""
        filename = f"{user_id}_{timestamp}_{file_type}{file_ext}"
        save_path = os.path.join(TEMP_DIR, filename)
        
        # Копируем файл
        if os.path.exists(file_path):
            import shutil
            shutil.copy2(file_path, save_path)
            return {
                "success": True,
                "path": save_path,
                "filename": filename,
                "original_path": file_path
            }
        return {"success": False, "error": "Файл не найден"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def generate_requirements_document(project_data: Dict, format: str = "txt") -> Optional[str]:
    """
    Генерирует документ с требованиями в указанном формате
    
    Args:
        project_data: Данные проекта
        format: Формат файла (txt, json, md)
    
    Returns:
        Путь к созданному файлу или None
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = project_data.get('project_name', 'Проект').replace(' ', '_')
        
        if format == "txt":
            filename = f"{project_name}_{timestamp}.txt"
            filepath = os.path.join(TEMP_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"БИЗНЕС-ТРЕБОВАНИЯ: {project_data.get('project_name', 'Проект')}\n")
                f.write("=" * 80 + "\n\n")
                
                if project_data.get('goal'):
                    f.write(f"ЦЕЛЬ ПРОЕКТА:\n{project_data.get('goal')}\n\n")
                
                if project_data.get('summary'):
                    f.write(f"ОПИСАНИЕ:\n{project_data.get('summary')}\n\n")
                
                if project_data.get('scope'):
                    f.write("SCOPE ПРОЕКТА:\n")
                    scope = project_data['scope']
                    if scope.get('in_scope'):
                        f.write("Входит в scope:\n")
                        for item in scope['in_scope']:
                            f.write(f"  • {item}\n")
                    if scope.get('out_scope'):
                        f.write("\nНе входит в scope:\n")
                        for item in scope['out_scope']:
                            f.write(f"  • {item}\n")
                    f.write("\n")
                
                if project_data.get('actors'):
                    f.write("УЧАСТНИКИ:\n")
                    for actor in project_data['actors']:
                        if isinstance(actor, dict):
                            f.write(f"  • {actor.get('role', '')}: {actor.get('description', '')}\n")
                        else:
                            f.write(f"  • {actor}\n")
                    f.write("\n")
                
                if project_data.get('trigger'):
                    f.write(f"ТРИГГЕР ПРОЦЕССА:\n{project_data.get('trigger')}\n\n")
                
                if project_data.get('expected_result'):
                    f.write(f"ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:\n{project_data.get('expected_result')}\n\n")
                
                if project_data.get('business_rules'):
                    f.write("БИЗНЕС-ПРАВИЛА:\n")
                    for i, rule in enumerate(project_data['business_rules'], 1):
                        f.write(f"{i}. {rule}\n")
                    f.write("\n")
                
                if project_data.get('kpi'):
                    f.write("KPI И МЕТРИКИ:\n")
                    for kpi in project_data['kpi']:
                        if isinstance(kpi, dict):
                            f.write(f"  • {kpi.get('metric', '')}: {kpi.get('target', '')} - {kpi.get('description', '')}\n")
                    f.write("\n")
                
                if project_data.get('requirements'):
                    f.write("ФУНКЦИОНАЛЬНЫЕ ТРЕБОВАНИЯ:\n")
                    for i, req in enumerate(project_data['requirements'], 1):
                        f.write(f"{i}. {req}\n")
                    f.write("\n")
                
                if project_data.get('use_cases'):
                    f.write("USE CASES:\n")
                    for uc in project_data['use_cases']:
                        if isinstance(uc, dict):
                            f.write(f"\n{uc.get('id', '')} - {uc.get('title', '')}\n")
                            f.write(f"Actor: {uc.get('actor', '')}\n")
                            f.write(f"Precondition: {uc.get('precondition', '')}\n")
                            f.write("Main Flow:\n")
                            for step in uc.get('main_flow', []):
                                f.write(f"  • {step}\n")
                            f.write(f"Postcondition: {uc.get('postcondition', '')}\n")
                    f.write("\n")
                
                if project_data.get('user_stories'):
                    f.write("USER STORIES:\n")
                    for us in project_data['user_stories']:
                        if isinstance(us, dict):
                            f.write(f"\n{us.get('id', '')}\n")
                            f.write(f"As {us.get('as', '')} I want {us.get('i_want', '')} so that {us.get('so_that', '')}\n")
                            if us.get('acceptance_criteria'):
                                f.write("Acceptance Criteria:\n")
                                for criteria in us['acceptance_criteria']:
                                    f.write(f"  ✓ {criteria}\n")
                    f.write("\n")
                
                if project_data.get('metrics'):
                    f.write("МЕТРИКИ ВЫПОЛНЕНИЯ:\n")
                    metrics = project_data['metrics']
                    f.write(f"  • Время формирования: {metrics.get('total_time_minutes', 0):.2f} минут\n")
                    f.write(f"  • Количество сообщений: {metrics.get('messages_count', 0)}\n")
            
            return filepath
        
        elif format == "json":
            filename = f"{project_name}_{timestamp}.json"
            filepath = os.path.join(TEMP_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
            
            return filepath
        
        elif format == "md":
            filename = f"{project_name}_{timestamp}.md"
            filepath = os.path.join(TEMP_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {project_data.get('project_name', 'Проект')}\n\n")
                
                if project_data.get('goal'):
                    f.write(f"## Цель проекта\n\n{project_data.get('goal')}\n\n")
                
                if project_data.get('summary'):
                    f.write(f"## Описание\n\n{project_data.get('summary')}\n\n")
                
                # Добавляем остальные секции в Markdown формате
                # (аналогично txt версии, но с Markdown разметкой)
            
            return filepath
        
        return None
    except Exception as e:
        print(f"Ошибка генерации документа: {e}")
        return None

def cleanup_old_files(max_age_hours: int = 24):
    """Удаляет старые файлы из временной папки"""
    try:
        current_time = datetime.now().timestamp()
        for filename in os.listdir(TEMP_DIR):
            filepath = os.path.join(TEMP_DIR, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > max_age_hours * 3600:
                    os.remove(filepath)
    except Exception as e:
        print(f"Ошибка очистки файлов: {e}")

def list_user_files(user_id: int) -> list:
    """Возвращает список файлов пользователя"""
    try:
        files = []
        if os.path.exists(TEMP_DIR):
            for filename in os.listdir(TEMP_DIR):
                if filename.startswith(f"{user_id}_"):
                    filepath = os.path.join(TEMP_DIR, filename)
                    if os.path.isfile(filepath):
                        file_size = os.path.getsize(filepath)
                        file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                        files.append({
                            "name": filename,
                            "path": filepath,
                            "size": file_size,
                            "modified": file_time
                        })
        return sorted(files, key=lambda x: x["modified"], reverse=True)
    except Exception as e:
        print(f"Ошибка получения списка файлов: {e}")
        return []

def get_file_by_name(filename: str) -> Optional[str]:
    """Возвращает путь к файлу по имени"""
    filepath = os.path.join(TEMP_DIR, filename)
    if os.path.exists(filepath) and os.path.isfile(filepath):
        return filepath
    return None

