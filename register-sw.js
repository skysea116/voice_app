// Регистрация сервис-воркера
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(registration => {
        console.log('ServiceWorker зарегистрирован: ', registration.scope);
        
        // Проверка обновлений
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          console.log('Обновление сервис-воркера найдено!');
          
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed') {
              if (navigator.serviceWorker.controller) {
                console.log('Новый контент доступен!');
                // Можно показать уведомление об обновлении
              }
            }
          });
        });
      })
      .catch(error => {
        console.log('Ошибка регистрации ServiceWorker: ', error);
      });
  });
  
  // Перехват сообщений о готовности
  let refreshing = false;
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (!refreshing) {
      refreshing = true;
      window.location.reload();
    }
  });
}