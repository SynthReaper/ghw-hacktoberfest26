import { test } from 'node:test';
import assert from 'node:assert';
import { GemmaNecromancer } from '../src/tools/gemma-necromancer.js';

test('GemmaNecromancer: modernizes vintage Python 2 urlfetch codebase', async () => {
  const necromancer = new GemmaNecromancer();
  const vintageFiles = {
    'urlfetch.py': `import urllib2\nprint "fetching..."\nexcept urllib2.HTTPError, e:\n  raise e\n`,
    'setup.py': `from distutils.core import setup\nsetup(name="urlfetch", install_requires=["simplejson"])\n`,
  };

  const result = await necromancer.resurrectCodebase(
    'urlfetch-test',
    vintageFiles,
    'Simple URL fetcher written in Python 2.7'
  );

  assert.strictEqual(result.repoName, 'urlfetch-test');
  assert.ok(result.targetRuntime.includes('Python 3.13'));
  assert.ok(result.revivedFiles.length > 0);

  const mainPy = result.revivedFiles.find(f => f.filename === 'urlfetch.py');
  assert.ok(mainPy);
  assert.ok(mainPy.content.includes('urllib.request'));
  assert.ok(mainPy.content.includes('class UrlFetcher:'));
  assert.ok(!mainPy.content.includes('print "fetching..."'));

  // Test suite and pyproject generated
  assert.ok(result.testSuiteContent.includes('def test_fetcher_init():'));
  assert.ok(result.pyprojectContent.includes('[project]'));
});

test('GemmaNecromancer: modernizes vintage cache daemon', async () => {
  const necromancer = new GemmaNecromancer();
  const vintageFiles = {
    'daemon.py': `import md5\nimport thread\nclass Cache(object):\n  pass\n`,
  };

  const result = await necromancer.resurrectCodebase(
    'cache-test',
    vintageFiles,
    'Simple LRU cache daemon'
  );

  const mainPy = result.revivedFiles.find(f => f.filename === 'daemon.py');
  assert.ok(mainPy);
  assert.ok(mainPy.content.includes('hashlib.sha256'));
  assert.ok(mainPy.content.includes('threading.Lock'));
});
