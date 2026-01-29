import PyInstaller.__main__
import os
import shutil

# Твой найденный путь к бинарникам
flet_bin_source = r"C:\Users\Deifo\Desktop\Dev\D1S3CT_x_SyncLine\project\.venv\Lib\site-packages\flet_desktop\app\flet"

if not os.path.exists(flet_bin_source):
    print(f"❌ ОШИБКА: Путь не найден: {flet_bin_source}")
    exit()

PyInstaller.__main__.run([
    'main.py',
    '--noconsole',
    '--name=SyncLine',
    '--icon=assets/icon.png',
    '--add-data=assets;assets',
    # Прописываем путь к бинарникам так, чтобы Flet нашел их внутри папки
    f'--add-data={flet_bin_source};flet_desktop/app/flet',
    '--collect-all=flet',
    '--collect-all=yadisk',
    '--collect-all=pystray',
    '--collect-all=watchdog',
    '--clean'
])

print("✅ Сборка завершена в папку dist/SyncLine")