const menuShow = document.querySelector('.menu');
const shadow = document.querySelector('.shadow-close')

document.addEventListener('DOMContentLoaded', () => {
    showMenu()
    closeMenu()
})

function showMenu() {
    const menuOpen = document.querySelector('.main-top-left > svg')
    if (!menuOpen || !menuShow) return;
    menuOpen.addEventListener('click', () => {
        menuShow.classList.add('menu-active');
        shadow.classList.add('visible');
    })
}

function closeMenu() {
    const buttonClose = document.querySelector('.menu-close');
    if (!buttonClose || !menuShow) return;
    buttonClose.addEventListener('click', () => {
        menuShow.classList.remove('menu-active');
        shadow.classList.remove('visible');
    })
    shadow?.addEventListener('click', () => {
        menuShow.classList.remove('menu-active');
        shadow.classList.remove('visible');
    });
}
