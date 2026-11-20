"""検査の照合の数を、同じ形の要約ファイルに書き出す（全検査共通）。

各検査は最後に Tally を一つ作り、save() で results/<資料名>/tally/<検査>[__<ラベル>].json に書く。
  compared       照合した数（「一致」か「食い違い」に判定できたもの）
  mismatched     食い違いの数（資料どうしの値が違ったもの。説明のある違いも含む）
  read_failures  読み取りの失敗・対応の取れなかったもの（照合の数に入れない。例：別の表の混同、頁番号の混入、行の対応なし）
  explained      mismatched のうち、資料の中に説明があるもの（注・正誤表・告知つきの差し替えなど）。分かる場合だけ
  note           一行の説明（何と何を照合したか）
使い方:
  from lib.tally import Tally
  t = Tally('gyakutai', 'c701', note='行・列の和と総数、表どうしの総数')
  t.ok(n); t.ng(n); t.fail(n); t.save()
既存の出力から書き起こした場合（検査を走らせ直していない場合）は source='adapter' を付ける。
"""
import json, os, hashlib, datetime

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Tally:
    def __init__(self, slug_dir, check, label='', note='', source='check', script=None):
        self.d = {'dir': slug_dir, 'check': check, 'label': label, 'note': note, 'source': source,
                  'compared': 0, 'mismatched': 0, 'explained': None, 'read_failures': 0}
        self.script = script

    def ok(self, n=1):
        self.d['compared'] += n

    def ng(self, n=1, explained=False):
        self.d['compared'] += n
        self.d['mismatched'] += n
        if explained:
            self.d['explained'] = (self.d['explained'] or 0) + n

    def fail(self, n=1):
        self.d['read_failures'] += n

    def set(self, compared, mismatched, read_failures=0, explained=None):
        self.d.update(compared=compared, mismatched=mismatched, read_failures=read_failures, explained=explained)

    def save(self):
        if self.script and os.path.exists(self.script):
            self.d['script_sha256'] = hashlib.sha256(open(self.script, 'rb').read()).hexdigest()
        self.d['written_utc'] = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        out = os.path.join(R, 'results', self.d['dir'], 'tally')
        os.makedirs(out, exist_ok=True)
        fn = self.d['check'] + (('__' + self.d['label']) if self.d['label'] else '') + '.json'
        json.dump(self.d, open(os.path.join(out, fn), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        return os.path.join(out, fn)
