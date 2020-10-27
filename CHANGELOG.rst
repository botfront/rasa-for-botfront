:desc: Rasa For Botfront Changelog

.. towncrier release notes start

[1.10.16-bf.1] - 2020-10-27
^^^^^^^^^^^^^^^^^^^^^

Improvements
--------
- `#32 <https://github.com/botfront/rasa-for-botfront/pull/32>`_: Move graphql slot interpolation to Rasa.
- `#29 <https://github.com/botfront/rasa-for-botfront/pull/29>`_: Add support for the augmentation factor in the train route.


[1.10.10-bf.4] - 2020-09-18
^^^^^^^^^^^^^^^^^^^^^

Features
--------
- `#28 <https://github.com/botfront/rasa-for-botfront/pull/28>`_: Determine required slots programmatically from graph.


[1.10.10-bf.3] - 2020-08-19
^^^^^^^^^^^^^^^^^^^^^

Bugfixes
--------
- `bd8b860 <https://github.com/botfront/rasa-for-botfront/commit/bd8b860c0435b52c0d391816e9a71d18e9c12ef4>`_: Fix language not associated with right model at training time.


[1.10.10-bf.2] - 2020-08-17
^^^^^^^^^^^^^^^^^^^^^

Features
--------
- `#27 <https://github.com/botfront/rasa-for-botfront/pull/27>`_: Include entity misclassifications in /model/test/intents route response.


[1.10.10-bf.1] - 2020-08-12
^^^^^^^^^^^^^^^^^^^^^

Improvements
--------
- `6fe19b2 <https://github.com/botfront/rasa-for-botfront/commit/6fe19b21d489d9b6468951ba5310799fe3daf8ba>`_: Make `output_channel` param of /trigger_intent route define input channel of triggered intent.
- `2210d2e <https://github.com/botfront/rasa-for-botfront/commit/2210d2e8db38a47991f7f202da6c01df2b4edf27>`_: Use full rasa installation in Dockerfile (use flag `--extras full`).
- `1227e21 <https://github.com/botfront/rasa-for-botfront/commit/1227e2171eabeed7818639318a2e4cca348ffc31>`_: Allow instance to boot regardless of exceptions incurred during initial model loading.
- `6e728d7 <https://github.com/botfront/rasa-for-botfront/commit/6e728d74b92dd0bd98fae63bd6d3e4e989b80c66>`_: Move multilingual interpreter logic to ensemble interpreter class.


[1.10.3-bf.3] - 2020-07-22
^^^^^^^^^^^^^^^^^^^^^

Features
--------
- `d16e75f <https://github.com/botfront/rasa-for-botfront/commit/d16e75fc1b4461bcdc1168ea7a16bf322f977ca7>`_: Support for image url text replacements in BotfrontTemplatedNaturalLanguageGenerator and GraphQLNaturalLanguageGenerator.


Improvements
--------
- `cbff36b <https://github.com/botfront/rasa-for-botfront/commit/cbff36b7704baecda63720473456777daad968a5>`_: Re-allow Rasa container to be run as non-root.


[1.10.3-bf.2] - 2020-07-13
^^^^^^^^^^^^^^^^^^^^^

Bugfixes
--------
- `#25 <https://github.com/botfront/rasa-for-botfront/pull/25>`_: Fix story fingerprinting resulting in overeager Core retraining. Base it off story file text content instead of StoryGraph.


[1.10.3-bf.1] - 2020-07-01
^^^^^^^^^^^^^^^^^^^^^

Bugfixes
--------
- `82ca6d7 <https://github.com/botfront/rasa-for-botfront/commit/82ca6d797d2c8ce4100bc026a6e7c29abce38a7d>`_: Fix error when bf_forms slot is not defined.
- `63ab95f <https://github.com/botfront/rasa-for-botfront/commit/63ab95f76df9af451d352f044817e9682488253b>`_: Fix behavior of custom key in messages in Webchat and Rest channels.

Improvements
------------
- `29ed2fe <https://github.com/botfront/rasa-for-botfront/commit/29ed2fe14c017c065dbed5901a2ce438c28790c3>`_: Forward bot messages to output channel when using /conversations/<conversation_id>/tracker/events route.
- `1d37e10 <https://github.com/botfront/rasa-for-botfront/commit/1d37e1032c9f1a0796b3b0576754bf459aed71ec>`_: Make RestPlus and WebchatPlus channels aliases of Rest and Webchat.


[1.10.1-bf.1] - 2020-06-17
^^^^^^^^^^^^^^^^^^^^^

Features
--------
- `#73 <https://github.com/botfront/rasa-for-botfront/pull/23>`_: Read and handle automated forms from Botfront.

Improvements
------------
- `#24 <https://github.com/botfront/rasa-for-botfront/pull/24>`_: Move `rasa-addons` repo to `rasa-for-botfront`.

