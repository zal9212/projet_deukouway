from django.shortcuts import render
from django.views import View

from apps.ai.services.chatbot_service import ChatbotService
from apps.ai.choices import AIModeChoices

SESSION_HISTORY_KEY = 'chatbot_widget_history'
MAX_HISTORY_MESSAGES = 10


class SupportHomeView(View):
    """
    Standard support page showing help center topics and FAQs.
    """
    def get(self, request):
        return render(request, 'pages/client/chat.html')


class ChatbotWidgetView(View):
    """
    Distraction-free page designed to be embedded in an iframe for the chatbot drawer.
    """
    def get(self, request):
        return render(request, 'support/chatbot_widget.html')


class ChatbotResponseView(View):
    """
    Point d'entrée HTMX du widget de chat public : délègue la réponse au Groq LLM
    (via ChatbotService), avec bascule automatique sur le moteur de secours local
    si l'API est indisponible. L'historique de la session est conservé pour donner
    du contexte multi-tours à l'assistant, y compris pour les visiteurs anonymes.
    """
    def post(self, request):
        user_message = request.POST.get('message', '').strip()

        history = request.session.get(SESSION_HISTORY_KEY, [])

        bot_reply, is_fallback = ChatbotService.ask_chatbot(
            user=request.user,
            message=user_message,
            history=history,
            mode=AIModeChoices.GENERAL_CHAT,
        )

        history.append({'role': 'user', 'content': user_message})
        history.append({'role': 'assistant', 'content': bot_reply})
        request.session[SESSION_HISTORY_KEY] = history[-MAX_HISTORY_MESSAGES:]

        context = {
            'user_message': request.POST.get('message', ''),
            'bot_reply': bot_reply,
            'is_fallback': is_fallback,
        }
        return render(request, 'support/partials/chat_message.html', context)
