import './style.css';

interface ContactFormData {
    name: string;
    phone: string;
    email: string;
    message: string;
}

if ('scrollRestoration' in history) {
    history.scrollRestoration = 'manual';
}

window.addEventListener('DOMContentLoaded', () => {
    window.scrollTo(0, 0);

    const form = document.getElementById('contactForm') as HTMLFormElement | null;
    const submitBtn = document.getElementById('submitBtn') as HTMLButtonElement | null;
    const responseDiv = document.getElementById('formResponse') as HTMLDivElement | null;
    const loader = submitBtn?.querySelector('.loader') as HTMLDivElement | null;
    const btnText = submitBtn?.querySelector('.btn-text') as HTMLSpanElement | null;

    if (!form || !submitBtn || !responseDiv) return;

    form.addEventListener('submit', async (event: Event) => {
        event.preventDefault();

        const nameInput = document.getElementById('name') as HTMLInputElement;
        const phoneInput = document.getElementById('phone') as HTMLInputElement;
        const emailInput = document.getElementById('email') as HTMLInputElement;
        const messageInput = document.getElementById('message') as HTMLTextAreaElement;

        const nameValue = nameInput.value.trim();
        const phoneValue = phoneInput.value.trim();
        const emailValue = emailInput.value.trim();
        const messageValue = messageInput.value.trim();

        responseDiv.classList.add('hidden');
        responseDiv.className = 'form-response';

        const nameRegex = /^[A-Za-zА-Яа-яЁё\s]{2,50}$/;
        if (!nameRegex.test(nameValue)) {
            showError('Пожалуйста, введите корректное имя (только буквы, от 2 символов)');
            return;
        }

        const phoneRegex = /^\+?[\d\s()+-]{10,20}$/;
        if (!phoneRegex.test(phoneValue)) {
            showError('Введите корректный номер телефона (например, +79991234567)');
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(emailValue)) {            showError('Пожалуйста, введите валидный адрес электронной почты');
            return;
        }

        if (messageValue.length < 5) {
            showError('Сообщение должно быть не короче 5 символов');
            return;
        }

        const formData: ContactFormData = {
            name: nameValue,
            phone: phoneValue,
            email: emailValue,
            message: messageValue
        };

        submitBtn.disabled = true;
        loader?.classList.remove('hidden');
        if (btnText) btnText.textContent = 'Отправка...';

        try {
            const targetUrl = `${window.location.origin}/api/contact`;

            const response = await fetch(targetUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Сервер вернул некорректный ответ. Проверьте статус бэкенда.');
            }

            const result = await response.json();

            if (response.ok && result.status === 'success') {
                responseDiv.textContent = result.message || 'Сообщение успешно отправлено!';
                responseDiv.classList.add('success-message');
                responseDiv.classList.remove('hidden');
                form.reset();
            } else {
                throw new Error(result.message || 'Ошибка отправки.');
            }
        } catch (error: any) {
            console.error('Ошибка:', error);
            showError(error.message.includes('fetch') 
                ? 'Ошибка соединения. Убедитесь, что сервер запущен локально или деплой активен.' 
                : error.message
            );
        } finally {
            submitBtn.disabled = false;
            loader?.classList.add('hidden');
            if (btnText) btnText.textContent = 'Отправить сообщение';
        }
    });

    function showError(message: string) {
        responseDiv!.textContent = message;
        responseDiv!.classList.add('error-message');
        responseDiv!.classList.remove('hidden');
    }
});