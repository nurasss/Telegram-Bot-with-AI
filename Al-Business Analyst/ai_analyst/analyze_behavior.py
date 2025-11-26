import csv
import os
from typing import Dict, List, Optional
from collections import Counter

# Путь к файлу по умолчанию
DEFAULT_BEHAVIOR_FILE = r"c:\Users\bulat\Downloads\поведенческие паттерны клиентов.csv"

def analyze_behavior_patterns(file_path: Optional[str] = None) -> Dict:
    """Анализирует CSV файл с поведенческими паттернами клиентов"""
    if file_path is None:
        file_path = DEFAULT_BEHAVIOR_FILE
    
    if not os.path.exists(file_path):
        return {"error": f"Файл не найден: {file_path}"}
    
    records = []
    os_changes = []
    phone_changes = []
    logins_7d = []
    logins_30d = []
    os_types = []
    phone_brands = []
    
    try:
        # Пробуем разные кодировки
        encodings = ['utf-8-sig', 'cp1251', 'windows-1251', 'utf-8']
        f = None
        for enc in encodings:
            try:
                f = open(file_path, 'r', encoding=enc)
                f.readline()
                f.seek(0)
                break
            except:
                if f:
                    f.close()
                continue
        
        if not f:
            return {"error": "Не удалось определить кодировку файла"}
        
        with f:
            reader = csv.reader(f, delimiter=';')
            header1 = next(reader)  # Пропускаем русский заголовок
            header2 = next(reader)  # Пропускаем английский заголовок
            
            for row in reader:
                if len(row) >= 19:
                    try:
                        record = {
                            'transdate': row[0],
                            'cst_dim_id': row[1],
                            'monthly_os_changes': int(float(row[2])) if row[2] and row[2] != '-1.0' else 0,
                            'monthly_phone_model_changes': int(float(row[3])) if row[3] and row[3] != '-1.0' else 0,
                            'last_phone_model': row[4],
                            'last_os': row[5],
                            'logins_last_7_days': int(float(row[6])) if row[6] and row[6] != '-1.0' else 0,
                            'logins_last_30_days': int(float(row[7])) if row[7] and row[7] != '-1.0' else 0,
                            'login_frequency_7d': float(row[8]) if row[8] and row[8] != '-1.0' else 0,
                            'login_frequency_30d': float(row[9]) if row[9] and row[9] != '-1.0' else 0,
                        }
                        records.append(record)
                        
                        os_changes.append(record['monthly_os_changes'])
                        phone_changes.append(record['monthly_phone_model_changes'])
                        logins_7d.append(record['logins_last_7_days'])
                        logins_30d.append(record['logins_last_30_days'])
                        
                        # Извлекаем бренд из модели телефона
                        phone_model = record['last_phone_model']
                        if phone_model:
                            if 'iPhone' in phone_model or 'iOS' in phone_model:
                                phone_brands.append('Apple')
                            elif 'Samsung' in phone_model:
                                phone_brands.append('Samsung')
                            elif 'Xiaomi' in phone_model:
                                phone_brands.append('Xiaomi')
                            elif 'Huawei' in phone_model:
                                phone_brands.append('Huawei')
                            elif 'Oppo' in phone_model or 'OPPO' in phone_model:
                                phone_brands.append('OPPO')
                            elif 'Vivo' in phone_model:
                                phone_brands.append('Vivo')
                            else:
                                phone_brands.append('Другое')
                        
                        # Извлекаем тип ОС
                        os_type = record['last_os']
                        if os_type:
                            if 'iOS' in os_type:
                                os_types.append('iOS')
                            elif 'Android' in os_type:
                                os_types.append('Android')
                            else:
                                os_types.append('Другое')
                    except (ValueError, IndexError) as e:
                        continue
        
        total = len(records)
        if total == 0:
            return {"error": "Не удалось прочитать данные из файла"}
        
        # Статистика по изменениям устройств
        avg_os_changes = sum(os_changes) / len(os_changes) if os_changes else 0
        avg_phone_changes = sum(phone_changes) / len(phone_changes) if phone_changes else 0
        
        # Статистика по логинам
        avg_logins_7d = sum(logins_7d) / len(logins_7d) if logins_7d else 0
        avg_logins_30d = sum(logins_30d) / len(logins_30d) if logins_30d else 0
        
        # Распределение брендов
        brand_counter = Counter(phone_brands)
        top_brands = dict(brand_counter.most_common(5))
        
        # Распределение ОС
        os_counter = Counter(os_types)
        os_distribution = dict(os_counter)
        
        # Клиенты с подозрительным поведением (много изменений устройств)
        suspicious_os = len([x for x in os_changes if x >= 3])
        suspicious_phone = len([x for x in phone_changes if x >= 3])
        
        # Клиенты с низкой активностью
        low_activity = len([x for x in logins_30d if x < 5])
        
        return {
            "total_records": total,
            "unique_clients": len(set([r['cst_dim_id'] for r in records])),
            "avg_os_changes": round(avg_os_changes, 2),
            "avg_phone_changes": round(avg_phone_changes, 2),
            "avg_logins_7d": round(avg_logins_7d, 2),
            "avg_logins_30d": round(avg_logins_30d, 2),
            "top_phone_brands": top_brands,
            "os_distribution": os_distribution,
            "suspicious_os_changes": suspicious_os,
            "suspicious_phone_changes": suspicious_phone,
            "low_activity_clients": low_activity,
            "suspicious_percentage": round((suspicious_os + suspicious_phone) / total * 100, 2) if total > 0 else 0
        }
    except Exception as e:
        return {"error": str(e)}

def get_behavior_statistics_summary(stats: Dict) -> str:
    """Форматирует статистику поведенческих паттернов для вывода"""
    if "error" in stats:
        return f"❌ Ошибка: {stats['error']}"
    
    # Форматирование топ брендов
    brands_text = "\n".join([f"  • {brand}: {count} ({count/stats['total_records']*100:.1f}%)" 
                             for brand, count in stats['top_phone_brands'].items()])
    
    # Форматирование ОС
    os_text = "\n".join([f"  • {os}: {count} ({count/stats['total_records']*100:.1f}%)" 
                         for os, count in stats['os_distribution'].items()])
    
    summary = (
        f"📊 **Анализ поведенческих паттернов клиентов:**\n\n"
        f"📈 **Общая статистика:**\n"
        f"• Всего записей: {stats['total_records']:,}\n"
        f"• Уникальных клиентов: {stats['unique_clients']:,}\n\n"
        f"📱 **Изменения устройств:**\n"
        f"• Среднее изменение ОС за месяц: {stats['avg_os_changes']:.2f}\n"
        f"• Среднее изменение модели телефона: {stats['avg_phone_changes']:.2f}\n"
        f"• Подозрительных изменений ОС (≥3): {stats['suspicious_os_changes']}\n"
        f"• Подозрительных изменений телефонов (≥3): {stats['suspicious_phone_changes']}\n\n"
        f"🔐 **Активность логинов:**\n"
        f"• Среднее логинов за 7 дней: {stats['avg_logins_7d']:.2f}\n"
        f"• Среднее логинов за 30 дней: {stats['avg_logins_30d']:.2f}\n"
        f"• Клиентов с низкой активностью (<5 логинов/месяц): {stats['low_activity_clients']}\n\n"
        f"📲 **Топ брендов телефонов:**\n{brands_text}\n\n"
        f"💻 **Распределение ОС:**\n{os_text}\n\n"
        f"⚠️ **Риски:** {stats['suspicious_percentage']:.2f}% клиентов имеют подозрительные паттерны"
    )
    return summary

if __name__ == "__main__":
    result = analyze_behavior_patterns()
    print("\n=== Анализ поведенческих паттернов ===")
    if "error" not in result:
        print(get_behavior_statistics_summary(result))
    else:
        print(result["error"])

