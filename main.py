import flet as ft
import time


def main(page: ft.Page):
    # --- Базовые настройки страницы ---
    page.title = "SyncLine x Yandex"
    page.window_title_bar_hidden = True
    page.window_bgcolor = ft.colors.TRANSPARENT
    page.bgcolor = ft.colors.TRANSPARENT
    page.window_width = 850
    page.window_height = 550
    page.window_resizable = False
    page.padding = 0

    # --- Логика выбора папки ---
    def on_directory_result(e: ft.FilePickerResultEvent):
        if e.path:
            selected_path_text.value = e.path
            log_info(f"Выбрана директория: {e.path}")
            page.update()

    file_picker = ft.FilePicker(on_result=on_directory_result)
    page.overlay.append(file_picker)

    # --- Функции логирования ---
    def log_info(message):
        timestamp = time.strftime("%H:%M:%S")
        info_list.controls.insert(0, ft.Text(f"[{timestamp}] {message}", color=ft.colors.WHITE70))
        page.update()

    def log_error(message):
        timestamp = time.strftime("%H:%M:%S")
        error_list.controls.insert(0, ft.Text(f"[{timestamp}] ERROR: {message}", color=ft.colors.RED_300))
        page.update()

    # --- Управление окном ---
    def close_app(e): page.window_close()

    def minimize_app(e):
        page.window_minimized = True
        page.update()

    # --- Трей (Работает железно в 0.19.0) ---
    try:
        page.tray_icon_name = "sync"
        page.tray_icon_menu_items = [
            ft.PopupMenuItem(text="Развернуть",
                             on_click=lambda _: setattr(page, "window_minimized", False) or page.update()),
            ft.PopupMenuItem(text="Выход", on_click=close_app),
        ]
    except Exception as e:
        print(f"Трей пока не поддался: {e}")

    # --- Элементы интерфейса ---

    # Шапка
    header = ft.WindowDragArea(
        content=ft.Container(
            content=ft.Row([
                # Левая часть: авторский бейдж
                ft.Container(
                    content=ft.Text(
                        "made by D1S3CT",
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
    selected_path_text = ft.Text("Папка не выбрана", italic=True, color=ft.colors.WHITE54)

    status_card = ft.Container(
        content=ft.Column([
            ft.Icon(name=ft.icons.DNS_ROUNDED, color="#2C3E50", size=80),

            # Строка с названием и настройками
            ft.Row([
                ft.Text("SyncLine", size=28, weight="bold", color="#2C3E50"),
                ft.IconButton(
                    icon=ft.icons.SETTINGS_OUTLINED,
                    icon_color="#2C3E50",
                    icon_size=20,
                    tooltip="Настройки",
                    on_click=lambda _: log_info("Открытие настроек...")
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),

            ft.Row([
                ft.ElevatedButton(
                    "Выбрать папку",
                    icon=ft.icons.FOLDER_OPEN_OUTLINED,
                    color="#2C3E50",
                    bgcolor=ft.colors.WHITE,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                ),
                ft.ElevatedButton(
                    "Запустить",
                    bgcolor="#2C3E50",  # Темная кнопка для акцента
                    color=ft.colors.WHITE,
                    on_click=lambda _: log_info("Запуск мониторинга...")
                ),
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

    page.add(main_layout)


if __name__ == "__main__":
    ft.app(target=main)