#!/usr/bin/env python
"""Генератор фидов: services.yaml → docs/feed.yml (YML для Яндекс.Вебмастер
«Товары и цены» и товарного каталога VK) + docs/index.html (человекочитаемый статус).

Только stdlib. Схема services.yaml плоская и известная — парсер заточен под неё.
Запуск: python generator.py
"""
import datetime
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, 'docs')


def parse_services_yaml(path):
    """Мини-парсер плоского YAML: секция shop (скаляры + список categories)
    и список services (список словарей). Комментарии поддерживаются."""
    shop, categories, services = {}, [], []
    cur_service = None
    section = None
    in_categories = False
    cur_cat = None
    with open(path, encoding='utf-8') as f:
        for raw in f:
            line = raw.rstrip('\n')
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            indent = len(line) - len(line.lstrip(' '))
            if indent == 0 and stripped.endswith(':'):
                section = stripped[:-1]
                in_categories = False
                cur_service = None
                continue
            if section == 'shop':
                if stripped == 'categories:':
                    in_categories = True
                    continue
                if in_categories:
                    if stripped.startswith('- '):
                        cur_cat = {}
                        categories.append(cur_cat)
                        stripped = stripped[2:]
                    if ':' in stripped:
                        k, v = stripped.split(':', 1)
                        cur_cat[k.strip()] = re.sub(r'\s+#.*$', '', v).strip()
                    continue
                if ':' in stripped and not stripped.startswith('- '):
                    k, v = stripped.split(':', 1)
                    shop[k.strip()] = re.sub(r'\s+#.*$', '', v).strip()
                continue
            if section == 'services':
                if stripped.startswith('- '):
                    cur_service = {}
                    services.append(cur_service)
                    stripped = stripped[2:]
                if cur_service is not None and ':' in stripped:
                    k, v = stripped.split(':', 1)
                    v = re.sub(r'\s+#.*$', '', v).strip()   # срезать инлайн-комментарии
                    cur_service[k.strip()] = v
    return shop, categories, services


def parse_int_or_none(v):
    v = (v or '').strip()
    if not v or v.lower() in ('null', 'none', '~'):
        return None
    digits = re.sub(r'[^0-9]', '', v)
    return int(digits) if digits else None


def xesc(s):
    return html.escape(str(s), quote=True)


def build_yml(shop, categories, services, gen_date, style='yandex'):
    """YML-фид. style='yandex' — классические офферы (slug id); style='vk' — ВК-стиль
    (числовой vk_id, price_type/price_unit/vkCategory/weight/dimensions/ae_stock,
    CDATA description) — структура скопирована с эталона vk.com/uslugi-*.?format=yml."""
    L = []
    L.append('<?xml version="1.0" encoding="UTF-8"?>')
    L.append(f'<yml_catalog date="{gen_date}">')
    L.append('  <shop>')
    L.append(f'    <name>{xesc(shop.get("name", ""))}</name>')
    L.append(f'    <company>{xesc(shop.get("company", ""))}</company>')
    L.append(f'    <url>{xesc(shop.get("url", ""))}</url>')
    L.append(f'    <email>{xesc(shop.get("email", ""))}</email>')
    L.append('    <currencies><currency id="RUB" rate="1"/></currencies>')
    L.append('    <categories>')
    for c in categories:
        L.append(f'      <category id="{xesc(c.get("id", ""))}">{xesc(c.get("name", ""))}</category>')
    L.append('    </categories>')
    L.append('    <offers>')
    included = 0
    skipped = []
    for s in services:
        price = parse_int_or_none(s.get('price_from'))
        if price is None:
            skipped.append(s.get('slug', '?'))
            continue
        url = f"https://doctor-shapovalov.ru/{s.get('slug', '')}/"
        vk_id = re.sub(r'[^0-9]', '', str(s.get('vk_id', ''))) or '0'
        price_str = f'{price:,}'.replace(',', ' ')
        if style == 'vk':
            # ВК-стиль (эталон: vk.com/uslugi-*.?format=yml)
            L.append(f'      <offer available="true" id="{vk_id}">')
            L.append(f'        <name>{xesc(s.get("name", ""))}</name>')
            L.append(f'        <url>{xesc(url)}</url>')
            L.append('        <price_type>2</price_type>')
            L.append('        <price_unit>0</price_unit>')
            L.append(f'        <price>{price}</price>')
            L.append('        <currencyId>RUB</currencyId>')
            L.append('        <vkCategory>2053</vkCategory>')
            L.append('        <weight>1.0</weight>')
            L.append('        <dimensions>20.0/20.0/20.0</dimensions>')
            L.append('        <ae_stock>5</ae_stock>')
            pic = (s.get('picture') or '').strip()
            if pic:
                L.append(f'        <picture>{xesc(pic)}</picture>')
            # VK ограничивает длину description (~256) — держим ≤190 с запасом
            base = xesc(s.get('description', ''))
            tail = f' Цена «от» {price_str} ₽ — точная смета «под ключ» на бесплатной консультации. Имеются противопоказания.'
            if len(base) + len(tail) > 190:
                budget = 190 - len(tail)
                base = base[:budget].rsplit(' ', 1)[0] + '…'
            L.append(f'        <description><![CDATA[{base}{tail}]]></description>')
        else:
            # Яндекс-стиль
            L.append(f'      <offer id="{xesc(s.get("slug", ""))}" available="true">')
            L.append(f'        <url>{xesc(url)}</url>')
            L.append(f'        <price>{price}</price>')
            L.append('        <currencyId>RUB</currencyId>')
            L.append(f'        <categoryId>{xesc(categories[0].get("id", "1") if categories else "1")}</categoryId>')
            pic = (s.get('picture') or '').strip()
            if pic:
                L.append(f'        <picture>{xesc(pic)}</picture>')
            L.append('        <typePrefix>Пластическая операция</typePrefix>')
            L.append(f'        <name>{xesc(s.get("name", ""))} — от {price_str} ₽</name>')
            L.append(f'        <description>{xesc(s.get("description", ""))}</description>')
        L.append('      </offer>')
        included += 1
    L.append('    </offers>')
    L.append('  </shop>')
    L.append('</yml_catalog>')
    return '\n'.join(L) + '\n', included, skipped


def build_index(shop, categories, services, gen_date, included, skipped):
    site = shop.get('url', '').rstrip('/')
    rows_on, rows_off = [], []
    for s in services:
        price = parse_int_or_none(s.get('price_from'))
        url = f"{site}/{s.get('slug', '')}/"
        d = xesc(s.get('description', ''))
        if price is not None:
            rows_on.append(f"<tr><td><a href='{xesc(url)}'>{xesc(s.get('name'))}</a></td>"
                           f"<td>от {price:,} ₽</td><td>{d}</td><td><code>{xesc(url)}</code></td></tr>")
        else:
            rows_off.append(f"<tr><td>{xesc(s.get('name'))}</td><td colspan='3'>⚠️ цена не указана (price_from: null) — услуга НЕ в фиде</td></tr>")
    return f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Фиды услуг — {xesc(shop.get('name', ''))}</title>
<style>
body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:1100px;margin:24px auto;padding:0 16px;color:#222}}
table{{border-collapse:collapse;width:100%;margin:12px 0}}
td,th{{border:1px solid #ddd;padding:7px 10px;text-align:left;font-size:14px;vertical-align:top}}
th{{background:#f4f5f7}} code{{background:#f0f0f0;padding:1px 4px;font-size:12px}}
.badge{{display:inline-block;background:#0d6efd;color:#fff;padding:2px 10px;border-radius:12px;font-size:13px;margin-right:8px}}
.warn{{background:#fff3cd}}
h1{{font-size:22px}} h2{{font-size:17px;margin-top:28px}}
</style></head><body>
<h1>Фиды услуг — {xesc(shop.get('name', ''))}</h1>
<p>Сгенерировано автоматически: <b>{gen_date}</b> (UTC). Источник: <code>services.yaml</code>.</p>
<p>
<span class="badge">Фид (YML): <a style="color:#fff" href="feed.yml">feed.yml</a></span>
<span class="badge">В фиде услуг: {included}</span>
<span class="badge" style="background:#dc3545">Ждут цены: {len(skipped)}</span>
</p>
<h2>Подключение</h2>
<ul>
<li><b>Яндекс.Вебмастер</b> → «Товары и цены» → добавить фид: <code>feed.yml</code></li>
<li><b>VK Реклама</b> → Каталоги → создать каталог → «По ссылке» → <code>feed.yml</code> (формат YML)</li>
</ul>
<h2>Услуги в фиде ({included})</h2>
<table><tr><th>Услуга</th><th>Цена</th><th>Описание</th><th>URL</th></tr>{''.join(rows_on)}</table>
<h2>Ждут цены ({len(skipped)})</h2>
<table class="warn"><tr><th>Услуга</th><th colspan="3">Действие</th></tr>{''.join(rows_off)}</table>
<p style="color:#777">Дисклеймер: ИМЕЮТСЯ ПРОТИВОПОКАЗАНИЯ, НЕОБХОДИМА КОНСУЛЬТАЦИЯ СПЕЦИАЛИСТА</p>
</body></html>
"""


def build_pixel_js(services, gen_date, pixel_id=None):
    """JS-сниппет событий пикселя VK: service_view (с product_id/цена из services.yaml —
    они совпадают с offer id фида, что требует динамический ретаргет), lead_form,
    phone_click, messenger_click. ID пикселя из services.yaml (shop.pixel_id)."""
    entries = []
    for s in services:
        price = parse_int_or_none(s.get('price_from'))
        vk_id = re.sub(r'[^0-9]', '', str(s.get('vk_id', '')))
        if price is not None and vk_id:
            entries.append(f'"{s["slug"]}": {{ id: {vk_id}, price: {price} }}')
    services_map = ',\n    '.join(entries)
    return f"""/* События пикселя VK Рекламы — doctor-shapovalov.ru
 * Сгенерировано из services.yaml {gen_date} UTC. НЕ РЕДАКТИРОВАТЬ ВРУЧНУЮ —
 * правится services.yaml в репо doctor-shapovalov-feeds.
 * События (созданы в кабинете VK → пиксель → События):
 *   service_view      — «Просмотр карточки товара»: люди, 2+ сек на странице услуги,
 *                       1 раз за сессию на услугу. Боты/мониторы отфильтрованы.
 *   price_page_view   — «Пользовательские конверсии»: страница /ceny
 *   lead_form         — «Оформление заявки (лид)»: успешная отправка формы
 *   phone_click       — «Контакт»: клик по телефону
 *   messenger_click   — «Контакт»: клик по мессенджеру
 */
(function () {{
  var PID = window.VK_PIXEL_ID || '{pixel_id}';
  /* 0. Фильтр ботов, мониторов доступности и авто-проверщиков — не считать служебные заходы */
  var ua = navigator.userAgent || '';
  if (navigator.webdriver || /bot|crawl|spider|slurp|monitor|uptime|headless|lighthouse|pagespeed|pingdom|gtmetrix|yandexbot|googlebot|bingbot|petalbot|facebookexternalhit|vktest/i.test(ua)) return;
  function goal(name, params) {{
    window._tmr = window._tmr || [];
    window._tmr.push({{ type: 'reachGoal', id: PID, goal: name, params: params || {{}} }});
  }}
  /* карта услуг: slug → числовой id каталога VK + цена (offer id в feed.xml) */
  var SERVICES = {{
    {services_map}
  }};
  /* 1. Страницы услуг и /ceny */
  var m = location.pathname.match(/^\\/([a-z-]+)\\/?$/);
  if (m) {{
    var slug = m[1];
    if (slug === 'ceny') {{
      goal('price_page_view');
    }}
    if (SERVICES[slug]) {{
      /* service_view: через 2 секунды на странице (отсекаем мгновенные отказы),
         1 раз за сессию на услугу (sessionStorage) */
      var key = 'vk_sv_' + slug;
      var fire = function () {{
        goal('service_view', {{ product_id: SERVICES[slug].id, price: SERVICES[slug].price, value: SERVICES[slug].price }});
      }};
      var seen = null;
      try {{ seen = sessionStorage.getItem(key); }} catch (e) {{}}
      if (!seen) {{
        setTimeout(function () {{
          try {{ sessionStorage.setItem(key, '1'); }} catch (e) {{}}
          fire();
        }}, 2000);
      }}
    }}
  }}
  /* 2. Отправка любой формы Tilda → lead_form */
  if (window.jQuery) {{
    window.jQuery(document).on('tildaform:afterSuccess', function () {{
      goal('lead_form');
    }});
  }}
  /* 3. Клик по телефону и мессенджерам */
  document.addEventListener('click', function (e) {{
    var a = e.target && e.target.closest && e.target.closest('a[href]');
    if (!a) return;
    var h = a.getAttribute('href') || '';
    if (h.indexOf('tel:') === 0) {{
      goal('phone_click');
    }} else if (/wa\\.me|whatsapp|t\\.me|tg\\.me|vk\\.me|vk\\.com\\/im|max\\.ru/i.test(h)) {{
      goal('messenger_click');
    }}
  }}, true);
}})();
"""


def main():
    shop, categories, services = parse_services_yaml(os.path.join(ROOT, 'services.yaml'))
    if not services:
        sys.exit('services.yaml: не найден список services')
    gen_date = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M')
    yml, included, skipped = build_yml(shop, categories, services, gen_date, style='yandex')
    vkml, _, _ = build_yml(shop, categories, services, gen_date, style='vk')
    index = build_index(shop, categories, services, gen_date, included, skipped)
    pixel_js = build_pixel_js(services, gen_date, pixel_id=shop.get('pixel_id', 'ВАШ_ID_ПИКСЕЛЯ'))
    os.makedirs(DOCS, exist_ok=True)
    with open(os.path.join(DOCS, 'feed.yml'), 'w', encoding='utf-8') as f:
        f.write(yml)
    with open(os.path.join(DOCS, 'feed.xml'), 'w', encoding='utf-8') as f:
        f.write(vkml)  # ВК-стиль: числовые vk_id + VK-поля (feed_type yandex парсится каталогом)
    with open(os.path.join(DOCS, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index)
    with open(os.path.join(DOCS, 'vk-pixel-events.js'), 'w', encoding='utf-8') as f:
        f.write(pixel_js)
    # XML-валидация
    import xml.etree.ElementTree as ET
    ET.fromstring(yml)
    print(f'OK: feed.yml + feed.xml ({included} услуг), index.html, vk-pixel-events.js | ждут цены: {", ".join(skipped) if skipped else "нет"}')


if __name__ == '__main__':
    main()
