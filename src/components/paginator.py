import flet as ft


@ft.control
class Paginator(ft.Row):
    def __init__(self, total_items=0, items_per_page=10, on_page_change=None):
        super().__init__()
        self.total_items = total_items
        self.items_per_page = items_per_page
        self.current_page = 1
        self.on_page_change = on_page_change

        self.page_count = self._calculate_page_count()

        self.alignment = ft.MainAxisAlignment.CENTER
        self.spacing = 10

        self.btn_prev = ft.IconButton(
            icon=ft.Icons.ARROW_BACK, on_click=self.prev_page, disabled=True
        )

        self.btn_next = ft.IconButton(
            icon=ft.Icons.ARROW_FORWARD,
            on_click=self.next_page,
            disabled=self.page_count <= 1,
        )

        self.text_display = ft.Text(
            value=self._get_display_text(), size=16, weight=ft.FontWeight.W_500
        )

    def _calculate_page_count(self):
        if self.total_items <= 0:
            return 1
        return (self.total_items + self.items_per_page - 1) // self.items_per_page

    def _get_display_text(self):
        return f"{self.current_page} / {self.page_count}"

    def prev_page(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self._update_state()
            self._trigger_callback()

    def next_page(self, e):
        if self.current_page < self.page_count:
            self.current_page += 1
            self._update_state()
            self._trigger_callback()

    def _update_state(self):
        try:
            self.text_display.value = self._get_display_text()

            self.btn_prev.disabled = self.current_page <= 1
            self.btn_next.disabled = self.current_page >= self.page_count

            self.text_display.update()
            self.btn_prev.update()
            self.btn_next.update()
        except RuntimeError:
            return

    def _trigger_callback(self):
        if self.on_page_change:
            self.on_page_change()

    def set_total_items(self, total_items):
        """Установить общее количество элементов"""
        self.total_items = total_items
        self._recalculate_pages()

    def set_items_per_page(self, items_per_page):
        """Установить количество элементов на странице"""
        self.items_per_page = items_per_page
        self._recalculate_pages()

    def set_pagination_params(self, total_items=None, items_per_page=None):
        """Установить параметры пагинации"""
        if total_items is not None:
            self.total_items = total_items
        if items_per_page is not None:
            self.items_per_page = items_per_page
        self._recalculate_pages()

    def _recalculate_pages(self):
        """Пересчитать количество страниц и обновить состояние"""
        old_page_count = self.page_count
        self.page_count = self._calculate_page_count()

        if self.page_count != old_page_count:
            if self.current_page > self.page_count:
                self.current_page = self.page_count
                self._trigger_callback()

        self._update_state()

    def set_current_page(self, page):
        """Установить текущую страницу"""
        if 1 <= page <= self.page_count and page != self.current_page:
            self.current_page = page
            self._update_state()
            self._trigger_callback()

    def get_current_page(self):
        """Получить текущую страницу"""
        return self.current_page

    def get_current_offset(self):
        """Получить текущий offset (смещение) для запроса данных"""
        if self.current_page <= 1:
            return 0
        return (self.current_page - 1) * self.items_per_page

    def get_current_range(self):
        """Получить диапазон элементов на текущей странице"""
        start = self.get_current_offset()
        end = min(start + self.items_per_page, self.total_items)
        return start, end

    def build(self):
        self.controls = [self.btn_prev, self.text_display, self.btn_next]
