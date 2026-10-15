# -*- coding: utf-8 -*-
import io
import json

BS = chr(92)
s = io.open(r'C:\Users\Administrator\Desktop\AI光学参赛\光学交互实验室_AI_v6.4.6.html',
            encoding='utf-8').read()
KEY = 'window.__S3D_LENS__ = "'
lines = s.split('\n')
li = [i for i, l in enumerate(lines) if l.startswith(KEY)][0]
old = lines[li][len('window.__S3D_LENS__ = '):-1]
v = json.loads(old)
print('decoded </script            :', v.count('</script'))
print('decoded </script (any case) :', v.lower().count('</script'))
print('old literal <' + BS + '/script count:', old.count('<' + BS + '/script'))
print('old literal <' + BS + '/ count      :', old.count('<' + BS + '/'))

t1 = json.dumps(v, ensure_ascii=False).replace('</script', '<' + BS + '/script')
t2 = json.dumps(v, ensure_ascii=False).replace('</', '<' + BS + '/')
print('only </script  parity=%s len=%d' % (t1 == old, len(t1)))
print('all </         parity=%s len=%d' % (t2 == old, len(t2)))

n = io.open(r'C:\Users\Administrator\Desktop\AI光学参赛\_extract_v646_lens.html', encoding='utf-8').read()
print('新场景 </script=%d   </=%d   len=%d' % (n.count('</script'), n.count('</'), len(n)))
