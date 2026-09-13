import {copyFileSync,mkdirSync} from 'node:fs';
mkdirSync('web/vendor',{recursive:true});
for (const name of ['three.module.js','three.core.js']) copyFileSync(`node_modules/three/build/${name}`,`web/vendor/${name}`);
copyFileSync('node_modules/three/examples/jsm/controls/OrbitControls.js','web/vendor/OrbitControls.js');
copyFileSync('node_modules/three/LICENSE','web/vendor/THREE-LICENSE.txt');
