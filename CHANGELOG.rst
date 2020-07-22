:desc: Rasa For Botfront Changelog

.. towncrier release notes start

[1.10.3-bf.3] - 2020-07-22
^^^^^^^^^^^^^^^^^^^^^

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

