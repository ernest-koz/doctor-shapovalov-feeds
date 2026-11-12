/* События пикселя VK Рекламы — doctor-shapovalov.ru
 * Сгенерировано из services.yaml 2026-11-12 19:01 UTC. НЕ РЕДАКТИРОВАТЬ ВРУЧНУЮ —
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
  /* карта услуг: slug → цена «от» (совпадает с offer id в feed.yml) */
  var SERVICES = {
    "abdomino": 300000,
    "blefaro": 45000,
    "face-lifting": 360000,
    "breast-enlargement": 320000,
    "breast-lifting": 250000,
    "breast-reduction": 320000,
    "breast-lipofilling": 100000,
    "liposuction": 50000,
    "lipofilling": 100000,
    "bodylift": 500000,
    "bisha": 50000,
    "hips": 100000,
    "shoulders": 100000,
    "lips": 65000,
    "scars": 20000
  };
  /* 1. Просмотр страницы услуги → service_view (динамический ретаргет) */
  var m = location.pathname.match(/^\/([a-z-]+)\/?$/);
  if (m && SERVICES[m[1]]) {
    goal('service_view', { product_id: m[1], price: SERVICES[m[1]], value: SERVICES[m[1]] });
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
