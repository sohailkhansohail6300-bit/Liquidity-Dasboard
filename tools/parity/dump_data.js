const fs=require('fs'),vm=require('vm');
const sb={window:{}};sb.window=sb;vm.createContext(sb);
vm.runInContext(fs.readFileSync(process.argv[2]+'/js/data.js','utf8'),sb);
process.stdout.write(JSON.stringify(sb.DBT_DATA));
