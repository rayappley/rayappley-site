/* In-page navigation: builds the "On this page" list from the h2 headings
   of a guide and highlights the section you are reading. */
(function () {
  function buildNav(nav) {
    var scope = nav.closest('[data-nav-scope]') || document;
    var headings = Array.prototype.slice.call(scope.querySelectorAll('.prose h2[id]'));
    var list = nav.querySelector('.page-nav-list');
    if (headings.length < 3 || !list) return;

    var links = headings.map(function (h) {
      var li = document.createElement('li');
      var a = document.createElement('a');
      a.className = 'chip';
      a.href = '#' + h.id;
      a.textContent = h.textContent;
      li.appendChild(a);
      list.appendChild(li);
      return a;
    });
    nav.hidden = false;

    function setActive(index) {
      links.forEach(function (a, i) {
        if (i === index) {
          a.setAttribute('aria-current', 'true');
          // keep the active chip visible in the phone scroller without moving the page
          var box = list.getBoundingClientRect(), r = a.getBoundingClientRect();
          if (list.scrollWidth > list.clientWidth && (r.left < box.left || r.right > box.right)) {
            list.scrollLeft += r.left - box.left - 16;
          }
        } else {
          a.removeAttribute('aria-current');
        }
      });
    }

    if (!('IntersectionObserver' in window)) return;
    var visible = new Set();
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var i = headings.indexOf(e.target);
        if (e.isIntersecting) visible.add(i); else visible.delete(i);
      });
      if (visible.size) {
        setActive(Math.min.apply(null, Array.from(visible)));
      } else {
        // between headings: the last heading above the reading line is the current section
        var current = -1;
        headings.forEach(function (h, i) { if (h.getBoundingClientRect().top < window.innerHeight * 0.3) current = i; });
        if (current > -1) setActive(current);
      }
    }, { rootMargin: '-15% 0px -65% 0px' });
    headings.forEach(function (h) { io.observe(h); });
  }

  document.querySelectorAll('.page-nav').forEach(buildNav);
})();
