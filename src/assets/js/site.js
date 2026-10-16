// Small enhancements; every page works without this file.
document.addEventListener('DOMContentLoaded', () => {
  // Mobile menu
  const menuBtn = document.querySelector('.menu-btn');
  const nav = document.getElementById('nav');
  if (menuBtn && nav) {
    menuBtn.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      menuBtn.setAttribute('aria-expanded', String(open));
    });
    nav.addEventListener('click', e => {
      if (e.target.closest('a')) { nav.classList.remove('open'); menuBtn.setAttribute('aria-expanded', 'false'); }
    });
  }

  // Copy IBAN
  document.querySelectorAll('.copy').forEach(btn => {
    const label = btn.textContent;
    const show = text => { btn.textContent = text; setTimeout(() => { btn.textContent = label; }, 1800); };
    btn.addEventListener('click', () => {
      const select = () => {
        const range = document.createRange();
        range.selectNodeContents(btn.previousElementSibling);
        const sel = getSelection(); sel.removeAllRanges(); sel.addRange(range);
        show(btn.dataset.fail);
      };
      if (!navigator.clipboard) return select();
      navigator.clipboard.writeText(btn.dataset.copy).then(() => show(btn.dataset.done), select);
    });
  });

  // Statutes: table of contents is a collapsible box on phones, always open on wide screens
  const toc = document.querySelector('.toc');
  if (toc) {
    const wide = matchMedia('(min-width: 960px)');
    const sync = () => { toc.open = wide.matches; };
    sync();
    wide.addEventListener('change', sync);
    toc.addEventListener('click', e => { if (e.target.closest('a') && !wide.matches) toc.open = false; });

    const links = new Map([...toc.querySelectorAll('a')].map(a => [a.getAttribute('href').slice(1), a]));
    const io = new IntersectionObserver(entries => {
      entries.forEach(en => {
        if (en.isIntersecting) {
          links.forEach(a => a.classList.remove('active'));
          links.get(en.target.id)?.classList.add('active');
        }
      });
    }, { rootMargin: '0px 0px -70% 0px' });
    document.querySelectorAll('.chapter').forEach(ch => io.observe(ch));
  }

  // Date fields in Latvian format dd.mm.gggg. Accepts 1.3.1980, 01-03-1980, 01/03/1980 or 01031980 and tidies it up.
  const parseDate = value => {
    const v = value.trim();
    const m = v.match(/^(\d{1,2})[.\-\/ ](\d{1,2})[.\-\/ ](\d{4})$/) || v.match(/^(\d{2})(\d{2})(\d{4})$/);
    if (!m) return null;
    const [d, mo, y] = [+m[1], +m[2], +m[3]];
    const date = new Date(y, mo - 1, d);
    const ok = date.getFullYear() === y && date.getMonth() === mo - 1 && date.getDate() === d
      && y >= 1900 && date <= new Date();
    return ok ? `${String(d).padStart(2, '0')}.${String(mo).padStart(2, '0')}.${y}` : null;
  };
  const dateInputs = [...document.querySelectorAll('input[data-date]')];
  const tidyDate = input => {
    const tidy = parseDate(input.value);
    if (tidy) input.value = tidy;
    input.setCustomValidity(!input.value || tidy ? '' : input.dataset.invalid);
  };
  dateInputs.forEach(input => {
    input.addEventListener('input', () => input.setCustomValidity(!input.value || parseDate(input.value) ? '' : input.dataset.invalid));
    input.addEventListener('change', () => tidyDate(input));
    input.addEventListener('blur', () => tidyDate(input));
  });

  // Join form: send with Web3Forms and show the result on the page
  const form = document.getElementById('join-form');
  if (form) {
    const msg = document.getElementById('form-msg');
    const ok = document.getElementById('form-ok');
    const btn = form.querySelector('button[type="submit"]');
    const label = btn.textContent;

    // Browser validation bubbles in Latvian instead of the browser's own language
    form.querySelectorAll('input:not([type="hidden"]), textarea').forEach(el => {
      el.addEventListener('invalid', () => {
        if (el.validity.valueMissing) el.setCustomValidity(el.type === 'checkbox' ? form.dataset.requiredCheck : form.dataset.required);
        else if (el.validity.typeMismatch && el.type === 'email') el.setCustomValidity(form.dataset.invalidEmail);
      });
      if (!el.hasAttribute('data-date')) {
        const clear = () => el.setCustomValidity('');
        el.addEventListener('input', clear);
        el.addEventListener('change', clear);
      }
    });

    form.addEventListener('submit', async e => {
      e.preventDefault();
      dateInputs.forEach(tidyDate);
      msg.hidden = true;
      if (!form.dataset.key) { msg.textContent = form.dataset.notConfigured; msg.hidden = false; return; }
      btn.disabled = true; btn.textContent = form.dataset.sending;
      try {
        // Sent as JSON: with multipart form data Web3Forms garbles Latvian letters in the field names (ā → Ä)
        const res = await fetch(form.action, {
          method: 'POST',
          body: JSON.stringify(Object.fromEntries(new FormData(form))),
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' }
        });
        const data = await res.json();
        if (!res.ok || !data.success) throw new Error(data.message || res.status);
        form.hidden = true; ok.hidden = false; ok.scrollIntoView({ block: 'center' });
      } catch (err) {
        msg.textContent = form.dataset.error; msg.hidden = false;
      } finally {
        btn.disabled = false; btn.textContent = label;
      }
    });
  }
});
