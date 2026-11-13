/* События пикселя VK Рекламы — doctor-shapovalov.ru
 * Сгенерировано из services.yaml 2026-11-13 15:45 UTC. НЕ РЕДАКТИРОВАТЬ ВРУЧНУЮ —
 * правится services.yaml в репо doctor-shapovalov-feeds.
 * В кабинете VK (Сайты → пиксель → События) заранее создать события:
 *   lead_form        — категория «Оформление заявки (лид)», условие «JS событие»
 *   phone_click      — категория «Контакт», «JS событие»
 *   messenger_click  — категория «Контакт», «JS событие»
 *   service_view     — категория «Просмотр карточки товара», «JS событие»
 */
(function () {
  var PID = window.VK_PIXEL_ID || '3814125';
  function goal(name, params) {
    window._tmr = window._tmr || [];
    window._tmr.push({ type: 'reachGoal', id: PID, goal: name, params: params || {} });
  }
  /* карта услуг: slug → числовой id каталога VK + цена (offer id в feed.xml) */
  var SERVICES = {
    "abdomino": { id: 1, price: 300000 },
    "blefaro": { id: 2, price: 45000 },
    "face-lifting": { id: 3, price: 360000 },
    "breast-enlargement": { id: 4, price: 320000 },
    "breast-lifting": { id: 5, price: 250000 },
    "breast-reduction": { id: 6, price: 320000 },
    "breast-lipofilling": { id: 7, price: 100000 },
    "liposuction": { id: 8, price: 50000 },
    "lipofilling": { id: 9, price: 100000 },
    "bodylift": { id: 10, price: 500000 },
    "bisha": { id: 11, price: 50000 },
    "hips": { id: 12, price: 100000 },
    "shoulders": { id: 13, price: 100000 },
    "lips": { id: 14, price: 65000 },
    "scars": { id: 15, price: 20000 }
  };
  /* 1. Просмотр страницы услуги → service_view (динамический ретаргет) */
  var m = location.pathname.match(/^\/([a-z-]+)\/?$/);
  if (m && SERVICES[m[1]]) {
    goal('service_view', { product_id: SERVICES[m[1]].id, price: SERVICES[m[1]].price, value: SERVICES[m[1]].price });
  }
  /* 2. Отправка любой формы Tilda → lead_form */
  if (window.jQuery) {
    window.jQuery(document).on('tildaform:afterSuccess', function () {
      goal('lead_form');
    });
  }
  /* 3. Клик по телефону и мессенджерам */
  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest && e.target.closest('a[href]');
    if (!a) return;
    var h = a.getAttribute('href') || '';
    if (h.indexOf('tel:') === 0) {
      goal('phone_click');
    } else if (/wa\.me|whatsapp|t\.me|tg\.me|vk\.me|vk\.com\/im|max\.ru/i.test(h)) {
      goal('messenger_click');
    }
  }, true);
})();
