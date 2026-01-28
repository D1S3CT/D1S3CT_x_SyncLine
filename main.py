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
        # Используем самый простой способ через создание объектов 'в лоб'
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
                ft.Text(" D1S3CT x SyncLine", weight="bold", size=14, color=ft.colors.WHITE),
                ft.Row([
                    ft.IconButton(ft.icons.MINIMIZE, on_click=minimize_app, icon_color=ft.colors.WHITE70),
                    ft.IconButton(ft.icons.CLOSE, on_click=close_app, icon_color=ft.colors.RED_400),
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(left=20, right=10),
            height=40,
        )
    )

    info_list = ft.ListView(expand=True, spacing=5)
    error_list = ft.ListView(expand=True, spacing=5)
    selected_path_text = ft.Text("Папка не выбрана", italic=True, color=ft.colors.WHITE54)

    # Центральный блок
    sync_icon = ft.Icon(name=ft.icons.SYNC_ROUNDED, color=ft.colors.BLUE_400, size=80)

    status_card = ft.Container(
        content=ft.Column([
            sync_icon,
            ft.Text("Cloud Synchronizer", size=24, weight="bold", color=ft.colors.WHITE),
            ft.Row([
                ft.ElevatedButton("Выбрать папку", icon=ft.icons.FOLDER_OPEN,
                                  on_click=lambda _: file_picker.get_directory_path()),
                ft.ElevatedButton("Запустить", bgcolor=ft.colors.BLUE_600, color=ft.colors.WHITE,
                                  on_click=lambda _: log_info("Служба синхронизации запущена...")),
            ], alignment=ft.MainAxisAlignment.CENTER),
            selected_path_text
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        expand=True
    )

    # Панель логов
    logs_panel = ft.Container(
        content=ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="События (INFO)", content=info_list),
                ft.Tab(text="Ошибки (ERRORS)", content=error_list),
            ],
        ),
        height=200,
        bgcolor=ft.colors.with_opacity(0.1, ft.colors.BLACK),
        padding=10,
        border_radius=ft.border_radius.only(bottom_left=15, bottom_right=15)
    )

    # Финальная сборка
    main_layout = ft.Container(
        content=ft.Column([header, status_card, logs_panel], spacing=0),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left, end=ft.alignment.bottom_right,
            colors=[ft.colors.GREY_900, ft.colors.BLACK]
        ),
        blur=30,
        border_radius=15,
        border=ft.border.all(1, ft.colors.WHITE10),
        expand=True
    )

    page.add(main_layout)


if __name__ == "__main__":
    ft.app(target=main)