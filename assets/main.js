const btn=document.querySelector('.menu-btn');
const nav=document.querySelector('nav');
if(btn&&nav){
  const close=()=>{nav.classList.remove('open');btn.setAttribute('aria-expanded','false');};
  btn.addEventListener('click',()=>{
    const open=!nav.classList.contains('open');
    nav.classList.toggle('open',open);
    btn.setAttribute('aria-expanded',String(open));
  });
  nav.addEventListener('click',e=>{if(e.target.closest('a'))close();});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')close();});
}
