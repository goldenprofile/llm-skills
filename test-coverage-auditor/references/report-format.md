# Формат отчёта аудита тестов

Без эмодзи.

```markdown
# Test Coverage Audit: [Название проекта]

## Резюме
- Всего тестов: X
- Качество: Y/10
- Критичных проблем: Z

## CRITICAL — Тесты, которые не тестируют

### [TST-001] Тест без assertions
Файл: `путь/к/файлу.py:строка`

` ` `python
def test_user_profile(self):
    response = self.client.get('/profile/')
    # Нет assert!
` ` `

Проблема: тест проходит всегда, ничего не проверяет.

Исправление:
` ` `python
def test_user_profile(self):
    response = self.client.get('/profile/')
    assert response.status_code == 200
    assert 'username' in response.json()
` ` `

### [TST-002] Mock без проверки вызова
Файл: `путь/к/файлу.py:строка`

Исправление:
` ` `python
@patch('app.services.send_notification')
def test_order_creation(self, mock_notify):
    create_order(data)
    mock_notify.assert_called_once()
` ` `

## HIGH — Непокрытый критический код

### [TST-003] Финансовые операции без тестов
Файлы без тестов:
- `app/payments/views.py:PaymentView`
- `app/billing/services.py:create_invoice`

Критичность: CRITICAL — финансовые операции без тестов.

## Skip-тесты

| Тест | Файл | Причина | Действие |
|------|------|---------|----------|
| test_old_feature | tests/test_legacy.py:45 | "TODO fix" | Исправить или удалить |

## Рекомендуемые действия

1. Срочно: добавить assertions в X тестов.
2. Высокий приоритет: покрыть тестами критичные модули (payments, auth).
3. Следующий шаг: проверить mock'и, добавить assert_called.
```
