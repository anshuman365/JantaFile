// Privacy-focused analytics
if (navigator.doNotTrack !== '1' && !document.cookie.includes('analytics_optout')) {
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-XXXXXX', { 
        anonymize_ip: true,
        allow_google_signals: false,
        allow_ad_personalization_signals: false
    });
}