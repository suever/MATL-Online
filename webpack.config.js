const webpack = require('webpack');
const path = require('path')

 /*
 * Webpack Plugins
 */
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const ManifestRevisionPlugin = require('manifest-revision-webpack-plugin');
 // take debug mode from the environment
const debug = (process.env.NODE_ENV !== 'production');
 // Development asset host (webpack dev server)
const publicHost = debug ? 'http://localhost:2992' : '';
 const rootAssetPath = './assets/';
 module.exports = {
  // configuration
  context: __dirname,
  entry: {
    main_js: './assets/js/main',
    main_css: [
      './node_modules/font-awesome/css/font-awesome.css',
      './node_modules/bootstrap/dist/css/bootstrap.css',
      './node_modules/datatables.net-bs/css/dataTables.bootstrap.css',
      './assets/css/style.css',
      './assets/css/vendor/drawer.css'
    ]
  },
  output: {
    path: __dirname + '/matl_online/static/build',
    publicPath: publicHost + '/static/build/',
    filename: '[name].[hash].js',
    chunkFilename: '[id].[hash].js'
  },
  resolve: {
    extensions: ['.js', '.jsx', '.css'],
    alias: {
      'bootstrap-drawer': path.join(__dirname, 'node_modules/bootstrap-drawer/js/drawer.js')
    }
  },
  devtool: debug ? 'inline-sourcemap' : 'source-map',
  devServer: {
    headers: { 'Access-Control-Allow-Origin': '*' }
  },
  module: {
    loaders: [
      { test: /\.html$/, loader: 'raw-loader' },
      { test: /\.less$/, loader: ExtractTextPlugin.extract({fallback: 'style-loader', use: 'css-loader!less-loader' }) },
      { test: /\.css$/, loader: ExtractTextPlugin.extract({fallback: 'style-loader', use: 'css-loader' }) },
      { test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/, loader: 'url-loader?limit=10000&mimetype=application/font-woff' },
      { test: /\.(ttf|eot|svg|png|jpe?g|gif|ico)(\?.*)?$/i,
        loader: 'file-loader?context=' + rootAssetPath + '&name=[path][name].[hash].[ext]' },
      { test: /\.js$/, exclude: /node_modules/, loader: 'babel-loader', query: { presets: ['es2015'], cacheDirectory: true } },
    ]
  },
  plugins: [
    new ExtractTextPlugin('[name].[hash].css'),
    new webpack.ProvidePlugin({
        $: 'jquery',
        jQuery: 'jquery',
        'window.jQuery': 'jquery',
        'window.$': 'jquery'
    }),
    new ManifestRevisionPlugin(__dirname + '/matl_online/webpack/manifest.json', {
      rootAssetPath,
      ignorePaths: ['/js', '/css']
    }),
  ].concat(debug ? [] : [
    // production webpack plugins go here
    new webpack.DefinePlugin({
      'process.env': {
        'NODE_ENV': JSON.stringify('production')
      }
    }),
  ])
}