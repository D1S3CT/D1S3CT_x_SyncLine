import flet as ft
import time
import json
import os
import yadisk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

# --- 1. Глобальные утилиты ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка чтения конфига: {e}")
            return {}
    return {}


def save_config(data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка записи конфига: {e}")

# --- 2. Основная логика приложения ---
def main(page: ft.Page):
    # Загружаем данные сразу при входе в main
    config = load_config()

    # --- Базовые настройки страницы ---
    page.title = "SyncLine x Yandex"
    page.window_title_bar_hidden = True
    page.window_bgcolor = ft.colors.TRANSPARENT
    page.bgcolor = ft.colors.TRANSPARENT
    page.window_width = 850
    page.window_height = 550
    page.window_resizable = False
    page.padding = 0

    btn_start = ft.ElevatedButton(
        "Запустить",
        bgcolor="#2C3E50",
        color=ft.Colors.WHITE,  # Сразу фиксим Warning на Colors
        on_click=lambda e: toggle_sync(e)
    )

    def toggle_sync(e):
        # Проверяем, существует ли живой наблюдатель
        is_running = hasattr(page, "observer") and page.observer and page.observer.is_alive()

        if not is_running:
            # Пытаемся запустить
            success = start_sync(None)

            if success:
                # Только если start_sync вернул True, меняем UI
                btn_start.text = "Остановить"
                btn_start.bgcolor = ft.Colors.RED_400
                status_icon.color = ft.Colors.GREEN_400
                log_info("Интерфейс обновлен: мониторинг активен.")
            else:
                # Если start_sync вернул False, кнопка остается прежней
                status_icon.color = ft.Colors.RED_400  # Мигнем красным в знак ошибки
                page.update()
                time.sleep(0.5)
                status_icon.color = "#2C3E50"

        else:
            # Логика остановки
            try:
                if page.observer:
                    page.observer.stop()
                    page.observer.join(timeout=1)

                page.observer = None
                btn_start.text = "Запустить"
                btn_start.bgcolor = "#2C3E50"
                status_icon.color = "#2C3E50"
                log_info("Синхронизация остановлена.")
            except Exception as stop_err:
                log_error(f"Ошибка при остановке: {stop_err}")

        page.update()


    cloud_folder_name = ft.TextField(
        label="Папка в облаке",
        value=config.get("cloud_folder", "SyncLine_Backup"),
        border_color="#3498DB"
    )

    access_token = ft.TextField(
        label="Yandex Token",
        password=True,
        can_reveal_password=True,
        value=config.get("token", ""),
        border_color="#3498DB"
    )

    # Принудительно превращаем интервал в целое число (int), чтобы слайдер не ругался
    raw_interval = config.get("interval", 5)
    sync_interval = ft.Slider(
        min=1, max=60, divisions=60,
        label="{value} мин",
        value=int(float(raw_interval))  # Безопасное приведение
    )

    # Путь к логам
    current_log_path = config.get("log_path", "logs/syncline.log")
    log_file_path = ft.Text(
        current_log_path,
        size=11, italic=True, color="#7F8C8D",
        overflow=ft.TextOverflow.ELLIPSIS, max_lines=1
    )

    # Путь к локальной папке
    selected_path_text = ft.Text(
        config.get("local_path", "Папка не выбрана"),
        italic=True, color="#7F8C8D"
    )

    page.selected_path_control = selected_path_text

    # --- Элементы управления (UI State) ---
    info_list = ft.ListView(expand=True, spacing=5)
    error_list = ft.ListView(expand=True, spacing=5)

    # --- Функции обработчики ---
    # Переменная для хранения наблюдателя (чтобы можно было остановить)
    page.observer = None


    def start_sync(e):
        # Используем атрибут страницы, который мы создали для борьбы с дублями
        local_path = page.selected_path_control.value
        token = access_token.value.strip()
        remote_folder = f"/{cloud_folder_name.value}"

        if local_path == "Папка не выбрана" or not token:
            log_error("Ошибка: Проверьте токен и выбор папки!")
            return

        y = yadisk.YaDisk(token=token)

        try:
            if not y.check_token():
                log_error("Токен невалиден!")
                return False

            log_info("Связь установлена. Проверка облачной папки...")
            if not y.exists(remote_folder):
                y.mkdir(remote_folder)
                log_info(f"Создана папка: {remote_folder}")

            class SyncHandler(FileSystemEventHandler):
                def on_created(self, event):
                    if not event.is_directory:
                        filename = os.path.basename(event.src_path)
                        try:
                            log_info(f"Загрузка: {filename}...")
                            with open(event.src_path, "rb") as f:
                                y.upload(f, f"{remote_folder}/{filename}", overwrite=True)
                            log_info(f"Успешно: {filename}")
                        except Exception as upload_err:
                            log_error(f"Ошибка загрузки {filename}: {upload_err}")

            # --- КРИТИЧЕСКИЙ ФИКС ДЛЯ PYTHON 3.13 ---
            def run_observer_safe():
                try:
                    # Создаем локальный объект, не привязанный к page напрямую при старте
                    obs = Observer()
                    obs.schedule(SyncHandler(), local_path, recursive=False)

                    # Самый важный момент: запуск без лишних проверок
                    obs.start()

                    # Сохраняем уже запущенный объект
                    page.sync_observer = obs

                    while True:
                        time.sleep(1)
                        if not obs.is_alive():
                            break
                except Exception as obs_err:
                    # Если здесь снова вылетит _ThreadHandle, значит 3.13 блокирует watchdog 3.0.0
                    print(f"Поток мониторинга упал: {obs_err}")

            t = threading.Thread(target=run_observer_safe, daemon=True)
            t.start()

            page.observer = Observer()
            page.observer.schedule(SyncHandler(), local_path, recursive=False)
            page.observer.start()

            log_info(f"💪 Мониторинг запущен: {local_path}")
            return True  # Успешный запуск!

        except Exception as ex:
            log_error(f"Ошибка старта: {ex}")
            return False  # Что-то пошло не так


    def write_to_file(level, message):
        # Берем путь из нашего текстового поля настроек
        path = log_file_path.value

        # Проверяем, существует ли папка для логов, если нет - создаем
        log_dir = os.path.dirname(path)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except:
                return  # Если не удалось создать папку, просто выходим

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"

        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Ошибка записи в файл: {e}")

    def log_info(message):
        timestamp = time.strftime("%H:%M:%S")
        # Вывод в интерфейс
        info_list.controls.insert(0, ft.Text(f"[{timestamp}] {message}", color="#2C3E50"))
        # Запись в файл
        write_to_file("INFO", message)
        page.update()

    def log_error(message):
        timestamp = time.strftime("%H:%M:%S")
        # Вывод в интерфейс
        error_list.controls.insert(0, ft.Text(f"[{timestamp}] ERROR: {message}", color=ft.colors.RED_300))
        # Запись в файл
        write_to_file("ERROR", message)
        page.update()

    def save_settings_to_file(e):
        new_config = {
            "cloud_folder": cloud_folder_name.value,
            "token": access_token.value,
            "interval": sync_interval.value,
            "log_path": log_file_path.value,
            "local_path": selected_path_text.value
        }
        save_config(new_config)
        log_info(f"Конфигурация сохранена в {CONFIG_FILE}")
        settings_dialog.open = False
        page.update()


    # --- Логика выбора папки ---
    def on_directory_result(e: ft.FilePickerResultEvent):
        if e.path:
            selected_path_text.value = e.path
            log_info(f"Локальная папка установлена: {e.path}")

            # Сразу обновляем конфиг, чтобы путь не потерялся
            current_config = load_config()
            current_config["local_path"] = e.path
            save_config(current_config)

            page.update()

    # Логика выбора папки для логов
    def on_logs_path_result(e: ft.FilePickerResultEvent):
        if e.path:
            log_file_path.value = f"{e.path}\\syncline.log"
            log_info(f"Путь логов изменен: {e.path}")
            page.update()

    # --- Pickers ---
    file_picker = ft.FilePicker(on_result=on_directory_result)
    logs_picker = ft.FilePicker(on_result=on_logs_path_result)
    page.overlay.append(file_picker)
    page.overlay.append(logs_picker)

    # --- Окна и диалоги ---
    settings_dialog = ft.AlertDialog(
        title=ft.Text("Настройки конфигурации"),
        content=ft.Column([
            cloud_folder_name,
            access_token,
            ft.Text("Интервал проверки (минуты):", size=12, weight="bold"),
            sync_interval,
            ft.Divider(),
            ft.Row([
                ft.Text("Файл логов:"),
                log_file_path,
                ft.IconButton(ft.icons.EDIT_DOCUMENT, icon_size=16, on_click=lambda _: logs_picker.get_directory_path())

            ])
        ], tight=True, spacing=15),
        actions=[
            ft.TextButton("Отмена", on_click=lambda _: setattr(settings_dialog, "open", False) or page.update()),
            ft.ElevatedButton("Сохранить", bgcolor="#2C3E50", color=ft.colors.WHITE, on_click=save_settings_to_file),
        ],
    )
    page.overlay.append(settings_dialog)

    # --- UI Компоненты ---
    def close_app(e): page.window_close()

    def minimize_app(e): page.window_minimized = True; page.update()

    # Трей
    try:
        page.tray_icon_name = "sync"
        page.tray_icon_menu_items = [
            ft.PopupMenuItem(text="Развернуть",
                             on_click=lambda _: setattr(page, "window_minimized", False) or page.update()),
            ft.PopupMenuItem(text="Выход", on_click=close_app),
        ]
    except:
        pass

    # Шапка
    header = ft.WindowDragArea(
        content=ft.Container(
            content=ft.Row([
                # Левая часть: авторский бейдж
                ft.Container(
                    content=ft.Text(
                        "made by D1S3CT Labs.",
                        size=11,
                        weight="w500",
                        color=ft.colors.BLACK45,  # Мягкий серый цвет
                        font_family="Verdana"  # Или стандартный для системы
                    ),
                    padding=ft.padding.only(left=5),
                ),
                # Правая часть: стандартные кнопки
                ft.Row([
                    ft.IconButton(ft.icons.MINIMIZE, on_click=minimize_app, icon_color=ft.colors.BLACK45, icon_size=18),
                    ft.IconButton(ft.icons.CLOSE, on_click=close_app, icon_color=ft.colors.RED_300, icon_size=18),
                ], spacing=0)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=ft.colors.WHITE,  # Теперь хедер белый
            padding=ft.padding.only(left=15, right=10),
            height=40,
            border_radius=ft.border_radius.only(top_left=15, top_right=15)
        )
    )

    info_list = ft.ListView(expand=True, spacing=5)
    error_list = ft.ListView(expand=True, spacing=5)

    # 1. Сначала выносим иконку в переменную, чтобы обращаться к ней из start_sync
    status_icon = ft.Icon(name=ft.icons.DNS_ROUNDED, color="#2C3E50", size=80)

    # 2. Теперь сам контейнер
    status_card = ft.Container(
        content=ft.Column([
            status_icon,  # Используем переменную вместо создания новой иконки

            # Строка с названием и настройками
            ft.Row([
                ft.Text("SyncLine", size=28, weight="bold", color="#2C3E50"),
                ft.IconButton(
                    icon=ft.icons.SETTINGS_OUTLINED,
                    icon_color="#2C3E50",
                    icon_size=20,
                    tooltip="Настройки",
                    on_click=lambda _: setattr(settings_dialog, "open", True) or page.update()
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),

            ft.Row([
                ft.ElevatedButton(
                    "Выбрать папку",
                    icon=ft.icons.FOLDER_OPEN_OUTLINED,
                    color="#2C3E50",
                    bgcolor=ft.colors.WHITE,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    on_click=lambda _: file_picker.get_directory_path()
                ),
                btn_start
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
            selected_path_text
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        expand=True
    )

    # Панель логов
    logs_panel = ft.Container(
        content=ft.Tabs(
            selected_index=0,
            label_color="#2C3E50",
            unselected_label_color="#95A5A6",
            indicator_color="#2C3E50",
            tabs=[
                ft.Tab(text="События (INFO)", content=info_list),
                ft.Tab(text="Ошибки (ERRORS)", content=error_list),
            ],
        ),
        height=220,
        bgcolor="#F8F9F9",  # Почти белый, но отделяет зону логов
        padding=10,
        border_radius=ft.border_radius.only(bottom_left=15, bottom_right=15)
    )

    # Финальная сборка (Весь фон белый)
    main_layout = ft.Container(
        content=ft.Column([header, status_card, logs_panel], spacing=0),
        bgcolor=ft.colors.WHITE,
        border_radius=15,
        border=ft.border.all(1, "#E5E7E9"),
        expand=True
    )

    page.add(ft.Container(
        content=ft.Column([header, status_card, logs_panel], spacing=0),
        bgcolor=ft.colors.WHITE, border_radius=15, border=ft.border.all(1, "#E5E7E9"), expand=True
    ))

if __name__ == "__main__":
    ft.app(target=main)