import csv
import os
from typing import Dict, List, Optional

# Путь к файлу по умолчанию
DEFAULT_TRANSACTIONS_FILE = r"c:\Users\bulat\Downloads\транзакции в Мобильном интернет Банкинге.csv"

def analyze_transactions(file_path: Optional[str] = None) -> Dict:
    """Анализирует CSV файл с транзакциями"""
    if file_path is None:
        file_path = DEFAULT_TRANSACTIONS_FILE
    
    if not os.path.exists(file_path):
        return {"error": f"Файл не найден: {file_path}"}
    
    transactions = []
    target_0 = 0
    target_1 = 0
    
    try:
        # Пробуем разные кодировки
        encodings = ['utf-8-sig', 'cp1251', 'windows-1251', 'utf-8']
        f = None
        for enc in encodings:
            try:
                f = open(file_path, 'r', encoding=enc)
                # Пробуем прочитать первую строку
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
                if len(row) >= 7:
                    transactions.append({
                        'cst_dim_id': row[0],
                        'transdate': row[1],
                        'transdatetime': row[2],
                        'amount': float(row[3]) if row[3] else 0,
                        'docno': row[4],
                        'direction': row[5],
                        'target': int(row[6]) if row[6] else 0
                    })
                    if row[6] == '1':
                        target_1 += 1
                    else:
                        target_0 += 1
        
        total = len(transactions)
        fraud_percent = (target_1 / total * 100) if total > 0 else 0
        
        # Статистика по суммам
        amounts = [t['amount'] for t in transactions]
        avg_amount = sum(amounts) / len(amounts) if amounts else 0
        max_amount = max(amounts) if amounts else 0
        min_amount = min(amounts) if amounts else 0
        
        # Статистика по мошенническим транзакциям
        fraud_transactions = [t for t in transactions if t['target'] == 1]
        fraud_amounts = [t['amount'] for t in fraud_transactions]
        avg_fraud_amount = sum(fraud_amounts) / len(fraud_amounts) if fraud_amounts else 0
        
        return {
            "total_transactions": total,
            "normal_transactions": target_0,
            "fraud_transactions": target_1,
            "fraud_percentage": round(fraud_percent, 2),
            "avg_amount": round(avg_amount, 2),
            "max_amount": round(max_amount, 2),
            "min_amount": round(min_amount, 2),
            "avg_fraud_amount": round(avg_fraud_amount, 2),
            "sample_transactions": transactions[:5]
        }
    except Exception as e:
        return {"error": str(e)}

def get_transaction_statistics_summary(stats: Dict) -> str:
    """Форматирует статистику для вывода"""
    if "error" in stats:
        return f"❌ Ошибка: {stats['error']}"
    
    summary = (
        f"📊 **Статистика транзакций:**\n\n"
        f"📈 Всего транзакций: {stats['total_transactions']:,}\n"
        f"✅ Нормальных: {stats['normal_transactions']:,} ({100 - stats['fraud_percentage']:.2f}%)\n"
        f"⚠️ Мошеннических: {stats['fraud_transactions']:,} ({stats['fraud_percentage']:.2f}%)\n\n"
        f"💰 **Суммы:**\n"
        f"• Средняя сумма: {stats['avg_amount']:,.2f} ₸\n"
        f"• Максимальная: {stats['max_amount']:,.2f} ₸\n"
        f"• Минимальная: {stats['min_amount']:,.2f} ₸\n"
        f"• Средняя мошенническая: {stats['avg_fraud_amount']:,.2f} ₸\n\n"
        f"🔍 **Вывод:** Средняя сумма мошеннических транзакций в {stats['avg_fraud_amount'] / stats['avg_amount']:.1f}x выше нормальных."
    )
    return summary

if __name__ == "__main__":
    result = analyze_transactions()
    print("\n=== Анализ транзакций ===")
    if "error" not in result:
        print(get_transaction_statistics_summary(result))
    else:
        print(result["error"])

