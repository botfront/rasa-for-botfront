# Rasa for Botfront

A fork to be used with **Botfront**, an open source chatbot platform built with Rasa.

For more information visit the [Botfront project on Github](https://github.com/botfront/botfront)


# Rasa Addons

## rasa_addons.core.channels.webchat.WebchatInput

### Example usage

```yaml
credentials:
  ...
  rasa_addons.core.channels.webchat.WebchatInput:
    session_persistence: true
    base_url: {{rasa_url}}
    socket_path: '/socket.io/'
  ...
```

## rasa_addons.core.channels.rest.BotfrontRestInput

Rest Input Channel with multilanguage and metadata support.

### Example usage

```yaml
credentials:
  ...
  rasa_addons.core.channels.rest.BotfrontRestInput:
    # POST {{rasa_url}}/webhooks/rest/webhook/
  ...
```

## rasa_addons.core.channels.bot_regression_test.BotRegressionTestInput:
Conversation testing channel. Simulates each user event in the input test stories as a message sent by a user, then compares the input story to the results from rasa. Returns a diff of the input story and output story with expected and actual events.

## Example usage

```yaml
credentials:
  ...
  rasa_addons.core.channels.bot_regression_test.BotRegressionTestInput: {}
    # POST {{rasa_url}} /webhooks/bot_regression_test/run
  ...
```

## rasa_addons.core.nlg.BotfrontTemplatedNaturalLanguageGenerator

Idential to Rasa's `TemplatedNaturalLanguageGenerator`, except in handles templates with a language key.

## rasa_addons.core.nlg.GraphQLNaturalLanguageGenerator

The new standard way to connect to the Botfront NLG endpoint. Note that support for the legacy REST endpoint is maintained for the moment. This feature is accessed by supplying a URL that doesn't contain the substring "graphql".

### Example usage

```yaml
endpoints:
  ...
  nlg:
    url: 'http://localhost:3000/graphql'
    type: 'rasa_addons.core.nlg.GraphQLNaturalLanguageGenerator'
  ...
```
