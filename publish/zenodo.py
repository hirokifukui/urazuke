"""Zenodo の DOI（2026-11-19、運営者の指示）。トークンは環境変数 ZENODO_TOKEN か、運営者の鍵のファイルの「Zenodoトークン」の次の行から読み、表示しない。
  python3 publish/zenodo.py check     … 認証を確かめる（読むだけ）
  python3 publish/zenodo.py reserve   … 下書き（非公開）を作り、DOI を予約する。publish/zenodo_state.json に記録
  python3 publish/zenodo.py release <tar.gz>  … 公開の日だけ：下書きにファイルを上げて公開する（GitHub の公開と同じ日に行う）
  python3 publish/zenodo.py newversion <tar.gz> <commit>  … 公開後、毎週：公開リポジトリが変わっていれば新しい版を作って公開する（2026-11-20）。
    その週の状態（取得元のハッシュの一覧を含む）を、第三者が日付を保証する形で残すため。commit が前回と同じなら何もしない。
下書きは公開されない。公開（release）は、GitHub を公開する日まで行わない（運営者の決定）。"""
import json, os, re, sys, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = 'https://zenodo.org/api'
KEYFILE = os.path.expanduser('~/Library/Mobile Documents/com~apple~CloudDocs/APIキー.txt')
STATE = os.path.join(ROOT, 'publish/zenodo_state.json')


def token():
    t = os.environ.get('ZENODO_TOKEN')
    if t: return t.strip()
    L = open(KEYFILE, encoding='utf-8').read().splitlines()
    for i, l in enumerate(L):
        if 'Zenodo' in l:
            for x in L[i:i + 3]:
                m = re.search(r'[A-Za-z0-9]{40,}', x)
                if m: return m.group(0)
    raise SystemExit('Zenodo のトークンが見つからない')


def req(method, path, data=None, raw=None, ctype='application/json'):
    url = path if path.startswith('http') else API + path
    body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
    r = urllib.request.Request(url, data=body, method=method, headers={'Authorization': 'Bearer ' + token(), 'Content-Type': ctype})
    with urllib.request.urlopen(r, timeout=120) as res:
        t = res.read(); return json.loads(t) if t else {}


def meta():
    z = json.load(open(os.path.join(ROOT, '.zenodo.json')))
    return {'metadata': {**z, 'prereserve_doi': True}}


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'check':
        d = req('GET', '/deposit/depositions?size=1'); print('認証できた。既存の deposition の数（1件まで表示）:', len(d))
    elif cmd == 'reserve':
        if os.path.exists(STATE): raise SystemExit('予約済み: ' + open(STATE).read())
        d = req('POST', '/deposit/depositions', meta())
        st = dict(id=d['id'], doi=d['metadata']['prereserve_doi']['doi'], bucket=d['links']['bucket'], state=d['state'], submitted=d['submitted'])
        json.dump(st, open(STATE, 'w'), indent=1); print(st)
    elif cmd == 'newversion':
        import datetime
        st = json.load(open(STATE)); fn, commit = sys.argv[2], sys.argv[3]
        if st.get('last_commit') == commit: print('公開リポジトリは前回の版から変わっていない：何もしない'); sys.exit(0)
        latest = st.get('latest_id', st['id'])
        d = req('POST', f"/deposit/depositions/{latest}/actions/newversion")
        draft = req('GET', d['links']['latest_draft'])
        for f in draft.get('files', []): req('DELETE', f"/deposit/depositions/{draft['id']}/files/{f['id']}")
        req('PUT', draft['links']['bucket'] + '/' + os.path.basename(fn), raw=open(fn, 'rb').read(), ctype='application/octet-stream')
        day = datetime.date.today().isoformat()
        z = json.load(open(os.path.join(ROOT, '.zenodo.json'))); z.update(version=day, publication_date=day)
        req('PUT', f"/deposit/depositions/{draft['id']}", {'metadata': z})
        p_ = req('POST', f"/deposit/depositions/{draft['id']}/actions/publish")
        st.update(latest_id=p_['id'], latest_doi=p_.get('doi') or p_['metadata'].get('doi'), last_commit=commit, last_version=day)
        json.dump(st, open(STATE, 'w'), indent=1); print('新しい版を公開した：', st['latest_doi'])
    elif cmd == 'release':
        st = json.load(open(STATE)); fn = sys.argv[2]
        req('PUT', st['bucket'] + '/' + os.path.basename(fn), raw=open(fn, 'rb').read(), ctype='application/octet-stream')
        d = req('POST', f"/deposit/depositions/{st['id']}/actions/publish"); st.update(state=d['state'], submitted=d['submitted']); json.dump(st, open(STATE, 'w'), indent=1); print(st)
