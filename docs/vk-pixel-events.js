/* События пикселя VK Рекламы — doctor-shapovalov.ru
 * Сгенерировано из services.yaml 2026-11-13 16:43 UTC. НЕ РЕДАКТИРОВАТЬ ВРУЧНУЮ —
 * правится services.yaml в репо doctor-shapovalov-feeds.
 * События (созданы в кабинете VK → пиксель → События):
 *   service_view      — «Просмотр карточки товара»: люди, 15+ секунд на странице услуги,
 *                       1 раз за сессию на услугу. Боты/мониторы/отказы отфильтрованы.
 *   price_page_view   — «Пользовательские конверсии»: 15+ секунд на странице /ceny
 *   lead_form         — «Оформление заявки (лид)»: успешная отправка формы
 *   phone_click       — «Контакт»: клик по телефону
 *   messenger_click   — «Контакт»: клик по мессенджеру
 */
(function () {
  var PID = window.VK_PIXEL_ID || '3814125';
  /* 0. Фильтр ботов, мониторов доступности и авто-проверщиков — не считать служебные заходы */
  var ua = navigator.userAgent || '';
  if (navigator.webdriver || /bot|crawl|spider|slurp|monitor|uptime|headless|lighthouse|pagespeed|pingdom|gtmetrix|yandexbot|googlebot|bingbot|petalbot|facebookexternalhit|vktest/i.test(ua)) return;
  function goal(name, params) {
    window._tmr = window._tmr || [];
    window._tmr.push({ type: 'reachGoal', id: PID, goal: name, params: params || {} });
  }
  /* событие через DELAY мс на странице, 1 раз за сессию (sessionStorage) */
  var DELAY = 15000;
  function delayedOnce(key, fn) {
    var seen = null;
    try { seen = sessionStorage.getItem(key); } catch (e) {}
    if (seen) return;
    setTimeout(function () {
      try { sessionStorage.setItem(key, '1'); } catch (e) {}
      fn();
    }, DELAY);
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
  /* 1. Страницы услуг и /ceny */
  var m = location.pathname.match(/^\/([a-z-]+)\/?$/);
  if (m) {
    var slug = m[1];
    if (slug === 'ceny') {
      delayedOnce('vk_pv_ceny', function () { goal('price_page_view'); });
    }
    if (SERVICES[slug]) {
      delayedOnce('vk_sv_' + slug, function () {
        goal('service_view', { product_id: SERVICES[slug].id, price: SERVICES[slug].price, value: SERVICES[slug].price });
      });
    }
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
