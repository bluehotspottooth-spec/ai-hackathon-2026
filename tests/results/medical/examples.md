# Medical test: side-by-side examples
Picked at random (seed 2026) from `all_translations.csv`. Scores and notes come from the blind AI judge, **not** a native speaker, so treat them as a first check. Every row is in `all_translations.csv`.

## Where VoiceBridge did better (1 cases)

Judge: VoiceBridge translated the medical term correctly, the baseline did not.

**M005 · Bengali · patient** · term: *lisinopril*

| | Text | Term OK | Accuracy (1-5) | Judge's note |
|---|---|---|---|---|
| English | and, and there's another one, , Lisinopril? Is that? Yeah, . I mean that's those two, I had, I've got them written down a wee bit of paper so. | | | |
| Baseline | এবং, এবং আরও একটি আছে, লিসিনপ্রফিল? সেটি কি? হ্যাঁ, মানে এই দুটি, আমার কাছে ছিল, আমার কাছে এক টুকরো কাগজে লেখা আছে। | ❌ | 4 | The medication name 'Lisinopril' is transliterated incorrectly as 'Lisinoprefil'. |
| VoiceBridge | আর, আর আরেকটি আছে, লিসিনোপ্রিল? সেটা কি? হ্যাঁ, মানে এই দুটি, আমার কাছে আছে, এগুলো একটি ছোট কাগজে লিখে এনেছি। | ✅ | 5 | - |

## Where VoiceBridge did WORSE (failures) (13 cases)

Judge preferred the plain baseline and scored VoiceBridge lower.

**M003 · Bengali · doctor** · term: *antibiotic*

| | Text | Term OK | Accuracy (1-5) | Judge's note |
|---|---|---|---|---|
| English | A script for antibiotics, which maybe use in next, twenty four to forty eight hours, if your symptoms don't get better. | | | |
| Baseline | অ্যান্টিবায়োটিকের একটি প্রেসক্রিপশন, যা আগামী চব্বিশ থেকে আটচল্লিশ ঘন্টার মধ্যে ব্যবহার করা যেতে পারে, যদি আপনার লক্ষণগুলির উন্নতি না হয়। | ✅ | 5 | - |
| VoiceBridge | অ্যান্টিবায়োটিকের একটি প্রেসক্রিপশন, যা হয়তো আগামী চব্বিশ থেকে আটচল্লিশ ঘণ্টার মধ্যে ব্যবহার করবেন, যদি আপনার লক্ষণগুলোর উন্নতি না হয়। | ✅ | 4 | Translation B incorrectly phrases the instructions as a statement of intent ('you will use') rather than an option/possibility ('can be used'). |

**M005 · Gujarati · patient** · term: *lisinopril*

| | Text | Term OK | Accuracy (1-5) | Judge's note |
|---|---|---|---|---|
| English | and, and there's another one, , Lisinopril? Is that? Yeah, . I mean that's those two, I had, I've got them written down a wee bit of paper so. | | | |
| Baseline | અને, અને ત્યાં બીજું એક છે, લિસિનોપ્રિલ? એ છે? હા. એટલે કે તે બે, મારી પાસે, મેં તે એક નાના કાગળ પર લખી રાખ્યા છે. | ✅ | 5 | - |
| VoiceBridge | અને, અને ત્યાં બીજી એક છે, લિસિનોપ્રિલ? શું તે? હા, . એટલે પેલી બે, મારી પાસે હતી, મેં તે કાગળના નાનકડા ટુકડા પર લખી રાખી છે એટલે. | ✅ | 4 | The phrase 'મારી પાસે હતી' (I had) incorrectly shifts the tense from the present perfect 'I've got' (meaning current possession) to past tense. |

**M004 · Persian · patient** · term: *diarrhoea*

| | Text | Term OK | Accuracy (1-5) | Judge's note |
|---|---|---|---|---|
| English | Uh, the, the first, the first day I had, you know a wee bit, of uh, , you know uh, you know the rot like, a wee bit of diarrhoea. | | | |
| Baseline | امم، روز، اولین، اولین روزی که داشتم، می‌دونی، یکم، امم، می‌دونی امم، می‌دونی مشکل معده داشتم، یه کم اسهال. | ✅ | 4 | Added 'stomach problem' which was not explicitly stated in the source text, though it fits the context. |
| VoiceBridge | روز اول، می‌دونی، کمی، ام، می‌دونی، ام، می‌دونی مثل حالت روال، کمی اسهال داشتم. | ✅ | 3 | The phrase 'like a routine state' is a poor translation of the filler 'the rot like', which in this context likely meant a sickness or colloquial description of illness rather than 'routine'. |

**M001 · Romanian · doctor** · term: *runny nose*

| | Text | Term OK | Accuracy (1-5) | Judge's note |
|---|---|---|---|---|
| English | Yeah, I can certainly hear you've got the sniffles. So, bit of a runny , bit of a runny nose, you mentioned. | | | |
| Baseline | Da, cu siguranță aud că ești răcit. Deci, puțin, ai menționat că îți curge puțin nasul. | ✅ | 5 | - |
| VoiceBridge | Da, cu siguranță aud că sunteți înfundat. Deci, ați menționat un nas care curge puțin. | ✅ | 4 | The translation 'sunteți înfundat' (congested/stuffed up) is slightly different from the original 'sniffles', which focuses more on the nasal discharge/runny aspect. |

**M003 · Urdu · doctor** · term: *antibiotic*

| | Text | Term OK | Accuracy (1-5) | Judge's note |
|---|---|---|---|---|
| English | A script for antibiotics, which maybe use in next, twenty four to forty eight hours, if your symptoms don't get better. | | | |
| Baseline | اینٹی بائیوٹکس کا نسخہ، جو اگلے چوبیس سے اڑتالیس گھنٹوں میں استعمال کیا جا سکتا ہے، اگر آپ کی علامات بہتر نہ ہوں۔ | ✅ | 5 | - |
| VoiceBridge | اینٹی بائیوٹک کا نسخہ، جو شاید اگلے چوبیس سے اڑتالیس گھنٹوں میں استعمال کرنا ہے، اگر آپ کی طبیعت بہتر نہیں ہوتی۔ | ✅ | 4 | The phrase 'maybe use' is translated as 'might have to be used', which is slightly less clear than the permissive tone of the English. |

**M001 · Gujarati · doctor** · term: *runny nose*

| | Text | Term OK | Accuracy (1-5) | Judge's note |
|---|---|---|---|---|
| English | Yeah, I can certainly hear you've got the sniffles. So, bit of a runny , bit of a runny nose, you mentioned. | | | |
| Baseline | હા, હું ચોક્કસ સાંભળી શકું છું કે તમને શરદી થઈ ગઈ છે. તો, તમે કહ્યું કે થોડું વહેતું, થોડું વહેતું નાક છે. | ✅ | 5 | - |
| VoiceBridge | હા, હું ચોક્કસ સાંભળી શકું છું કે તમને શરદી થઈ છે. એટલે, થોડું વહેતું, તમે થોડું વહેતું નાક હોવાનું કહ્યું. | ✅ | 4 | Slightly less natural phrasing for describing the symptoms. |

## Where BOTH got the medical term wrong (0 cases)

Neither system translated the key term correctly.
