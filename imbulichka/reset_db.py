import os
import shutil

def reset_database():
    """Пересоздать базу данных"""
    
    # Удаляем папку data если существует
    if os.path.exists('data'):
        try:
            shutil.rmtree('data')
            print("🗑️ Папка data удалена")
        except Exception as e:
            print(f"❌ Ошибка удаления папки: {e}")
    
    # Импортируем базу данных чтобы создать заново
    from utils.verification import db
    print("✅ База данных пересоздана")
    
    # Проверяем таблицы
    db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = db.cursor.fetchall()
    print(f"✅ Созданы таблицы: {[t[0] for t in tables]}")
    
    db.close()

if __name__ == "__main__":
    print("🔄 Пересоздаю базу данных...")
    reset_database()
    print("✅ Готово! Запустите бота: python main.py")