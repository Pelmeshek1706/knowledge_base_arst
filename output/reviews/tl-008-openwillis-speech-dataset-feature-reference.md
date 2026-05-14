# TL-008 OpenWillis PDF Review

- Source: `data/openwillis_speech_dataset_feature_reference.pdf`
- Extraction model: `qwen2.5-1.5b-instruct`
- Embedding model: `Qwen/Qwen3-Embedding-0.6B`
- Chunks: `15`

## Document Summary

Speech characteristics version 3.3 released on March 19, 2026, with dependencies and license Justification. The document provides details on various measures such as turns, summary files, dynamic columns added at runtime, and sentence-transformers.

## Document Tags

- openwillis-speech [openwillis-speech]
- speech-characteristics [speech-characteristics]
- dataset-feature-reference [dataset-feature-reference]
- project [project]
- code-scopes [code-scopes]
- turn-level [turn-level]
- utterance-list [utterance-list]
- feature-inputs [feature-inputs]
- speech_characteristics [speech_characteristics]
- v3.3 [v3.3]
- NLTK [nltk]
- spaCy [spacy]
- Pronoun [pronoun]
- DET [det]
- word_coherence [word_coherence]
- word_coherence_5 [word_coherence_5]
- word_coherence_10 [word_coherence_10]
- speech_turns [speech_turns]
- pause_duration [pause_duration]
- turn_length_minutes [turn_length_minutes]
- words_per_min [words_per_min]
- syllables_per_min [syllables_per_min]
- speech_analysis [speech_analysis]
- metrics [metrics]
- articulation_rate [articulation_rate]
- sentiment_scores [sentiment_scores]
- VADER_analyzer [vader_analyzer]
- speech characteristics [speech characteristics]
- moving-average type-token ratio [moving-average type-token ratio]
- first-person tokens [first-person tokens]
- sentiment interactions [sentiment interactions]
- repetition measures [repetition measures]
- sentence tangentiality [sentence tangentiality]
- coherence [coherence]
- predictability [predictability]
- turn-to-turn tangentiality [turn-to-turn tangentiality]
- semantic perplexity [semantic perplexity]
- interrupt flag [interrupt flag]
- speech_data [speech_data]
- file_level_rate_measures [file_level_rate_measures]
- sentiment_analysis [sentiment_analysis]
- VADER sentiment [vader sentiment]
- lexical diversity [lexical diversity]
- first-person interaction [first-person interaction]
- spaCy lemmatization [spacy lemmatization]
- repetition [repetition]
- variability [variability]
- turns [turns]
- speaker attribution [speaker attribution]
- tangentiality [tangentiality]
- perplexity [perplexity]
- turn-to-turn [turn-to-turn]
- slopes [slopes]
- interrupted [interrupted]
- speech [speech]
- characteristics [characteristics]
- version [version]
- release [release]
- inputs [inputs]
- outputs [outputs]
- summ_df [summ_df]
- sentence_transformers [sentence_transformers]
- dependency_license [dependency_license]
- lexicalrichness [lexicalrichness]
- VADER_sentiment [vader_sentiment]
- transformers [transformers]
- dependency [dependency]
- license justification [license justification]
- PyTorch [pytorch]
- transformer [transformer]
- coherence models [coherence models]
- simplemma [simplemma]
- Ukrainian lemmatization [ukrainian lemmatization]
- lexicon matching [lexicon matching]

## Document Entities

- openwillis-speech | type=Project | normalized=openwillis-speech | chunks=76d31999-d5c2-5b48-a85e-1b5af1f678dd
- speech-characteristics | type=Technology | normalized=speech-characteristics | chunks=76d31999-d5c2-5b48-a85e-1b5af1f678dd
- openwillis/openwillis-speech/src/openwillis/speech | type=Project | normalized=openwillis/openwillis-speech/src/openwillis/speech | chunks=1e355239-2813-5b12-926d-cb743d092c82, 371d1ab0-1b03-56d4-b588-2730997cfc93
- Mar 19, 2026 | type=Date | normalized=mar 19, 2026 | chunks=6882256a-d685-5eca-ae1c-6c7cc8778396, 6b73a7d9-5fcf-5857-a077-330cceab986b
- Speech characteristics v3.3 | type=DocumentType | normalized=speech characteristics v3.3 | chunks=6882256a-d685-5eca-ae1c-6c7cc8778396, 6b73a7d9-5fcf-5857-a077-330cceab986b
- Speech turns | type=Topic | normalized=speech turns | chunks=e264cc6f-6c9a-5abc-8efe-c199f5d9c864
- Word coherence | type=Technology | normalized=word coherence | chunks=e264cc6f-6c9a-5abc-8efe-c199f5d9c864
- Pause duration | type=Technology | normalized=pause duration | chunks=e264cc6f-6c9a-5abc-8efe-c199f5d9c864
- Turn length in minutes | type=DocumentType | normalized=turn length in minutes | chunks=e264cc6f-6c9a-5abc-8efe-c199f5d9c864
- Words per minute | type=DocumentType | normalized=words per minute | chunks=e264cc6f-6c9a-5abc-8efe-c199f5d9c864
- Syllables per minute | type=DocumentType | normalized=syllables per minute | chunks=e264cc6f-6c9a-5abc-8efe-c199f5d9c864
- llables_per_min | type=Technology | normalized=llables_per_min | chunks=6a0cd881-8a47-51f1-bb38-da229a120f17
- speech_percentage | type=Technology | normalized=speech_percentage | chunks=6a0cd881-8a47-51f1-bb38-da229a120f17
- mean_pause_length | type=Technology | normalized=mean_pause_length | chunks=6a0cd881-8a47-51f1-bb38-da229a120f17
- pause_variability | type=Technology | normalized=pause_variability | chunks=6a0cd881-8a47-51f1-bb38-da229a120f17
- mattr_5 | type=Technology | normalized=mattr_5 | chunks=b41e19ad-aa25-5a2e-8e66-f14f39360328, 88e628ee-240d-503b-8254-5186624ed776
- mattr_10 | type=Technology | normalized=mattr_10 | chunks=b41e19ad-aa25-5a2e-8e66-f14f39360328, 88e628ee-240d-503b-8254-5186624ed776
- mattr_25 | type=Technology | normalized=mattr_25 | chunks=b41e19ad-aa25-5a2e-8e66-f14f39360328, 88e628ee-240d-503b-8254-5186624ed776
- mattr_50 | type=Technology | normalized=mattr_50 | chunks=b41e19ad-aa25-5a2e-8e66-f14f39360328, 88e628ee-240d-503b-8254-5186624ed776
- mattr_100 | type=Technology | normalized=mattr_100 | chunks=b41e19ad-aa25-5a2e-8e66-f14f39360328, 88e628ee-240d-503b-8254-5186624ed776
- LexicalRichness.mattr() | type=Technology | normalized=lexicalrichness.mattr() | chunks=b41e19ad-aa25-5a2e-8e66-f14f39360328
- spaCy | type=Technology | normalized=spacy | chunks=b41e19ad-aa25-5a2e-8e66-f14f39360328
- sentiment_vader_pos | type=Technology | normalized=sentiment_vader_pos | chunks=88e628ee-240d-503b-8254-5186624ed776
- sentiment_vader_neg | type=Technology | normalized=sentiment_vader_neg | chunks=88e628ee-240d-503b-8254-5186624ed776
- sentiment_vader_neu | type=Technology | normalized=sentiment_vader_neu | chunks=88e628ee-240d-503b-8254-5186624ed776
- sentiment_vader_overall | type=Technology | normalized=sentiment_vader_overall | chunks=88e628ee-240d-503b-8254-5186624ed776
- first_person_percentage | type=Technology | normalized=first_person_percentage | chunks=88e628ee-240d-503b-8254-5186624ed776
- word_repeat_percentage | type=Technology | normalized=word_repeat_percentage | chunks=b3b13c80-49bf-5074-99e0-789d6756a819
- phrase_repeat_percentage | type=Technology | normalized=phrase_repeat_percentage | chunks=b3b13c80-49bf-5074-99e0-789d6756a819
- word_coherence_mean | type=Technology | normalized=word_coherence_mean | chunks=b3b13c80-49bf-5074-99e0-789d6756a819
- word_coherence_var | type=Technology | normalized=word_coherence_var | chunks=b3b13c80-49bf-5074-99e0-789d6756a819
- word_coherence_5_mean | type=Technology | normalized=word_coherence_5_mean | chunks=b3b13c80-49bf-5074-99e0-789d6756a819
- word_coherence_5_var | type=Technology | normalized=word_coherence_5_var | chunks=b3b13c80-49bf-5074-99e0-789d6756a819
- word_coherence_10_mean | type=Technology | normalized=word_coherence_10_mean | chunks=b3b13c80-49bf-5074-99e0-789d6756a819
- word_coherence_10_var | type=Technology | normalized=word_coherence_10_var | chunks=b3b13c80-49bf-5074-99e0-789d6756a819
- word_coherence_variability_2_mean | type=Technology | normalized=word_coherence_variability_2_mean | chunks=b3b13c80-49bf-5074-99e0-789d6756a819
- word_coherence_variability_10_var | type=Technology | normalized=word_coherence_variability_10_var | chunks=b3b13c80-49bf-5074-99e0-789d6756a819
- num_turns | type=Technology | normalized=num_turns | chunks=b3b13c80-49bf-5074-99e0-789d6756a819
- num_one_word_turns | type=Technology | normalized=num_one_word_turns | chunks=b3b13c80-49bf-5074-99e0-789d6756a819
- openwillis/speech | type=Project | normalized=openwillis/speech | chunks=2a6319f5-9b46-52a8-895a-e229ca7e3aa6
- 08:35 AM | type=Date | normalized=08:35 am | chunks=6b73a7d9-5fcf-5857-a077-330cceab986b
- Mar 19, 2026 08:35 AM Speech characteristics v3.3 | type=DocumentType | normalized=mar 19, 2026 08:35 am speech characteristics v3.3 | chunks=1fc98a36-f46e-5eb9-a128-a2ec7408f0ef
- PyTorch | type=Technology | normalized=pytorch | chunks=1fc98a36-f46e-5eb9-a128-a2ec7408f0ef
- simplemma | type=Technology | normalized=simplemma | chunks=1fc98a36-f46e-5eb9-a128-a2ec7408f0ef

## Top Chunk Tags

- speech (3 chunk(s))
- turn-level (2 chunk(s))
- v3.3 (2 chunk(s))
- nltk (2 chunk(s))
- spacy (2 chunk(s))
- word_coherence (2 chunk(s))
- pause_duration (2 chunk(s))
- coherence (2 chunk(s))
- turns (2 chunk(s))
- characteristics (2 chunk(s))
- openwillis-speech (1 chunk(s))
- speech-characteristics (1 chunk(s))
- dataset-feature-reference (1 chunk(s))
- project (1 chunk(s))
- code-scopes (1 chunk(s))
- utterance-list (1 chunk(s))
- feature-inputs (1 chunk(s))
- speech_characteristics (1 chunk(s))
- pronoun (1 chunk(s))
- det (1 chunk(s))
- word_coherence_5 (1 chunk(s))
- word_coherence_10 (1 chunk(s))
- speech_turns (1 chunk(s))
- turn_length_minutes (1 chunk(s))
- words_per_min (1 chunk(s))

## Top Chunk Entities

- Project: openwillis/openwillis-speech/src/openwillis/speech (2 chunk(s))
- Date: mar 19, 2026 (2 chunk(s))
- DocumentType: speech characteristics v3.3 (2 chunk(s))
- Technology: mattr_5 (2 chunk(s))
- Technology: mattr_10 (2 chunk(s))
- Technology: mattr_25 (2 chunk(s))
- Technology: mattr_50 (2 chunk(s))
- Technology: mattr_100 (2 chunk(s))
- Project: openwillis-speech (1 chunk(s))
- Technology: speech-characteristics (1 chunk(s))
- Topic: speech turns (1 chunk(s))
- Technology: word coherence (1 chunk(s))
- Technology: pause duration (1 chunk(s))
- DocumentType: turn length in minutes (1 chunk(s))
- DocumentType: words per minute (1 chunk(s))
- DocumentType: syllables per minute (1 chunk(s))
- Technology: llables_per_min (1 chunk(s))
- Technology: speech_percentage (1 chunk(s))
- Technology: mean_pause_length (1 chunk(s))
- Technology: pause_variability (1 chunk(s))
- Technology: lexicalrichness.mattr() (1 chunk(s))
- Technology: spacy (1 chunk(s))
- Technology: sentiment_vader_pos (1 chunk(s))
- Technology: sentiment_vader_neg (1 chunk(s))
- Technology: sentiment_vader_neu (1 chunk(s))

## First 3 Chunk Summaries

### Chunk 0 (page=1)
- Summary: Speech characteristics v3.3 dataset feature reference for openwillis-speech project.
- Tags: openwillis-speech, speech-characteristics, dataset-feature-reference, project, code-scopes
- Entities: openwillis-speech (Project), speech-characteristics (Technology)
### Chunk 1 (page=1)
- Summary: The code path builds turn-level feature inputs from the full utterance list when `speaker_label` is provided, even though it's not a strict single-speaker slice.
- Tags: turn-level, utterance-list, feature-inputs
- Entities: openwillis/openwillis-speech/src/openwillis/speech (Project)
### Chunk 2 (page=2)
- Summary: Speech characteristics v3.3
- Tags: speech_characteristics, v3.3, NLTK, spaCy, Pronoun, DET, word_coherence, word_coherence_5, word_coherence_10
- Entities: Mar 19, 2026 (Date), Speech characteristics v3.3 (DocumentType)

Full JSON payload: `/Users/pelmeshek1706/Desktop/projects/knowledge_agent/output/reviews/tl-008-openwillis-speech-dataset-feature-reference.json`