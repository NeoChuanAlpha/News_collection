/**
 * 新闻分析系统主JavaScript文件
 */

// 页面加载完成后执行
$(document).ready(function() {
    // 激活当前导航项
    activateNavItem();
    
    // 初始化工具提示
    $('[data-toggle="tooltip"]').tooltip();
    
    // 返回顶部按钮
    initBackToTop();
});

/**
 * 激活当前导航项
 */
function activateNavItem() {
    // 获取当前路径
    const path = window.location.pathname;
    
    // 移除所有激活状态
    $('.navbar-nav .nav-item').removeClass('active');
    
    // 根据路径激活对应的导航项
    if (path === '/') {
        $('.navbar-nav .nav-item:first-child').addClass('active');
    } else {
        $('.navbar-nav .nav-item').each(function() {
            const href = $(this).find('.nav-link').attr('href');
            if (path.startsWith(href) && href !== '/') {
                $(this).addClass('active');
            }
        });
    }
}

/**
 * 初始化返回顶部按钮
 */
function initBackToTop() {
    // 创建返回顶部按钮
    const $backToTop = $('<button>', {
        id: 'back-to-top',
        class: 'btn btn-primary btn-sm',
        html: '<i class="bi bi-arrow-up"></i>',
        css: {
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            display: 'none',
            zIndex: 1000
        }
    });
    
    // 添加到页面
    $('body').append($backToTop);
    
    // 滚动事件
    $(window).scroll(function() {
        if ($(this).scrollTop() > 300) {
            $backToTop.fadeIn();
        } else {
            $backToTop.fadeOut();
        }
    });
    
    // 点击事件
    $backToTop.click(function() {
        $('html, body').animate({ scrollTop: 0 }, 300);
        return false;
    });
}

/**
 * 格式化日期时间
 * @param {Date|string} date 日期对象或日期字符串
 * @param {string} format 格式化模式，默认为 'YYYY-MM-DD HH:mm:ss'
 * @returns {string} 格式化后的日期字符串
 */
function formatDateTime(date, format = 'YYYY-MM-DD HH:mm:ss') {
    if (!(date instanceof Date)) {
        date = new Date(date);
    }
    
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    
    return format
        .replace('YYYY', year)
        .replace('MM', month)
        .replace('DD', day)
        .replace('HH', hours)
        .replace('mm', minutes)
        .replace('ss', seconds);
}

/**
 * 显示加载中提示
 * @param {string} containerId 容器ID
 * @param {string} message 提示消息
 */
function showLoading(containerId, message = '加载中...') {
    const $container = $('#' + containerId);
    
    $container.html(`
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">加载中...</span>
            </div>
            <p class="mt-2">${message}</p>
        </div>
    `);
}

/**
 * 显示错误提示
 * @param {string} containerId 容器ID
 * @param {string} message 错误消息
 */
function showError(containerId, message) {
    const $container = $('#' + containerId);
    
    $container.html(`
        <div class="alert alert-danger" role="alert">
            <i class="bi bi-exclamation-triangle-fill"></i> ${message}
        </div>
    `);
}

/**
 * 显示成功提示
 * @param {string} containerId 容器ID
 * @param {string} message 成功消息
 */
function showSuccess(containerId, message) {
    const $container = $('#' + containerId);
    
    $container.html(`
        <div class="alert alert-success" role="alert">
            <i class="bi bi-check-circle-fill"></i> ${message}
        </div>
    `);
}

/**
 * 复制文本到剪贴板
 * @param {string} text 要复制的文本
 * @returns {Promise<boolean>} 是否复制成功
 */
function copyToClipboard(text) {
    return navigator.clipboard.writeText(text)
        .then(() => true)
        .catch(() => false);
}

/**
 * 防抖函数
 * @param {Function} func 要执行的函数
 * @param {number} wait 等待时间（毫秒）
 * @returns {Function} 防抖处理后的函数
 */
function debounce(func, wait = 300) {
    let timeout;
    
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 节流函数
 * @param {Function} func 要执行的函数
 * @param {number} limit 限制时间（毫秒）
 * @returns {Function} 节流处理后的函数
 */
function throttle(func, limit = 300) {
    let inThrottle;
    
    return function executedFunction(...args) {
        if (!inThrottle) {
            func(...args);
            inThrottle = true;
            setTimeout(() => {
                inThrottle = false;
            }, limit);
        }
    };
}

/**
 * 获取URL参数
 * @param {string} name 参数名
 * @returns {string|null} 参数值，不存在则返回null
 */
function getUrlParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

/**
 * 设置URL参数
 * @param {string} name 参数名
 * @param {string} value 参数值
 */
function setUrlParam(name, value) {
    const url = new URL(window.location.href);
    url.searchParams.set(name, value);
    window.history.replaceState({}, '', url);
}

/**
 * 删除URL参数
 * @param {string} name 参数名
 */
function removeUrlParam(name) {
    const url = new URL(window.location.href);
    url.searchParams.delete(name);
    window.history.replaceState({}, '', url);
} 