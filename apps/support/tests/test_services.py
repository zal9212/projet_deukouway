from django.test import TestCase
from apps.accounts.models import User
from apps.support.models import SupportCategory
from apps.support.services.services import SupportService
from apps.support.services.exceptions import TicketAlreadyClosed

class SupportServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@test.com", password="password")
        self.admin = User.objects.create_superuser(email="admin@test.com", password="password")
        self.category = SupportCategory.objects.create(name="Billing")

    def test_create_ticket(self):
        ticket = SupportService.create_ticket(self.user, self.category, "Help", "I need help")
        self.assertEqual(ticket.status, 'OPEN')

    def test_reply_ticket(self):
        ticket = SupportService.create_ticket(self.user, self.category, "Help", "I need help")
        msg = SupportService.reply_ticket(ticket, self.admin, "Sure, helping now.")
        self.assertEqual(msg.ticket, ticket)
        # Admin replying should set to IN_PROGRESS
        self.assertEqual(ticket.status, 'IN_PROGRESS')

    def test_close_ticket(self):
        ticket = SupportService.create_ticket(self.user, self.category, "Help", "I need help")
        ticket = SupportService.close_ticket(ticket, self.admin)
        self.assertEqual(ticket.status, 'CLOSED')
        
        with self.assertRaises(TicketAlreadyClosed):
            SupportService.reply_ticket(ticket, self.user, "Wait!")
