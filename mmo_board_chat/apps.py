from django.apps import AppConfig


class MmoBoardChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mmo_board_chat'

    def ready(self):
        # Импортируем сигналы только после полной загрузки приложения
        import mmo_board_chat.signals
