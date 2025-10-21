// Основные JavaScript функции для SoulMirror

// Получаем CSRF токен для AJAX запросов
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Глобальный спиннер загрузки
const GlobalLoader = {
    element: null,

    init: function() {
        this.element = document.getElementById('globalLoader');
    },

    show: function(text = 'Загрузка...') {
        if (!this.element) this.init();
        if (this.element) {
            const loaderText = this.element.querySelector('.loader-text');
            if (loaderText) loaderText.textContent = text;
            this.element.style.display = 'flex';
        }
    },

    hide: function() {
        if (!this.element) this.init();
        if (this.element) {
            this.element.style.display = 'none';
        }
    }
};

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    GlobalLoader.init();

    // Показываем спиннер при переходе по ссылкам навигации
    const navLinks = document.querySelectorAll('.nav-menu a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Показываем спиннер только для внутренних ссылок
            if (!link.getAttribute('href').startsWith('http')) {
                GlobalLoader.show('Загрузка страницы...');
            }
        });
    });

    // Показываем спиннер при отправке форм без специальных индикаторов
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Проверяем, есть ли у формы свой спиннер
            const hasOwnSpinner = form.querySelector('.btn-loader');
            if (!hasOwnSpinner) {
                GlobalLoader.show('Обработка данных...');
            }
        });
    });

    console.log('SoulMirror загружен');
});

// Скрываем спиннер после полной загрузки страницы
window.addEventListener('load', function() {
    // Небольшая задержка для плавности
    setTimeout(() => {
        GlobalLoader.hide();
    }, 100);
});

// Экспортируем GlobalLoader для использования в других скриптах
window.GlobalLoader = GlobalLoader;
