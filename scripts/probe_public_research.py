"""Guest-only live research fixture for an already isolated DAIA lab VM.

Do not run on the host: imports downloaded package code. Requires the fixed
credential-free CONNECT relay at 10.0.2.102:3128 and a disposable /work directory.
The external service, not this script, enforces destination and network policy.
"""
import http.client,ssl,json,pathlib,hashlib,sys
proxy=('10.0.2.102',3128)
def fetch(host,path,limit):
 c=http.client.HTTPSConnection(*proxy,context=ssl.create_default_context(),timeout=15);c.set_tunnel(host,443)
 try:
  c.request('GET',path,headers={'User-Agent':'DAIA-public-research-test'})
  r=c.getresponse();assert r.status==200
  data=r.read(limit+1);assert len(data)<=limit
  return data
 finally:c.close()
root=pathlib.Path('/work/research');root.mkdir(exist_ok=True)
doc=fetch('docs.python.org','/3/builtins/stdtypes.html',1000000)
(root/'stdtypes.html').write_bytes(doc)
meta=json.loads(fetch('pypi.org','/pypi/packaging/25.0/json',100000))
wheel=next(x for x in meta['urls'] if x['filename']=='packaging-25.0-py3-none-any.whl')
from urllib.parse import urlsplit
u=urlsplit(wheel['url']);assert u.scheme=='https' and u.hostname=='files.pythonhosted.org' and not u.query and not u.fragment
content=fetch(u.hostname,u.path,200000);assert hashlib.sha256(content).hexdigest()==wheel['digests']['sha256']
p=root/wheel['filename'];p.write_bytes(content);sys.path.insert(0,str(p))
from packaging.version import Version
assert Version('1.10')>Version('1.9') and Version('1')==Version('1.0')
result={'documentation_bytes':len(doc),'documentation_sha256':hashlib.sha256(doc).hexdigest(),'dependency':'packaging','version':'25.0','wheel_sha256':hashlib.sha256(content).hexdigest(),'dependency_import_and_checks':True}
(root/'result.json').write_text(json.dumps(result));print(json.dumps(result))
