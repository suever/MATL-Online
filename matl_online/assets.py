"""Javascript and CSS assets for the application."""

from flask_assets import Bundle, Environment

css = Bundle(
    'css/style.css',
    filters='yui_css',
    output='public/css/common.css'
)

js = Bundle(
    'js/main.js',
    filters='yui_js',
    output='public/js/common.js'
)

vendor_css = Bundle(
    'vendor/css/bootstrap-drawer.min.css',
    filters='yui_css',
    output='public/vendor/common.css'
)

vendor_js = Bundle(
    'vendor/js/autosize.min.js',
    'vendor/js/drawer.min.js',
    'vendor/js/jquery.hotkeys.min.js',
    output='public/vendor/common.js'
)

assets = Environment()

assets.register('js_all', js)
assets.register('css_all', css)
assets.register('js_vendor', vendor_js)
assets.register('css_vendor', vendor_css)
