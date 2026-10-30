---
createdDate: 2026-10-30
---
核心思路：用浏览器向 8080 端口发请求之后，先在我的程序通过调用 deepseek 判断情绪是什么，再根据情绪选择参考音频，然后发送给 9880 端口，交给 GSV 合成音频。

首先先看 TtsController.java ：
```java
//TtsController.java

@GetMapping("/tts")
public ResponseEntity<byte[]> tts(@RequestParam String text,
								  @RequestParam(required = false) String emotion) {
	if (emotion == null) {
	emotion = emotionService.classify(text);
}

byte[] wav = ttsService.synthesize(text, emotion);
return ResponseEntity.ok()
		.contentType(MediaType.parseMediaType("audio/wav"))
		.body(wav);
}
```

8080 端口接收到请求之后，会去寻找 emotion 类型（11 行代码），如果没有找到，就会进入下面的 if 语句，调用 emotionService 的服务，判断这个文本的情绪。

接下来看 EmotionService.java 里面的 classify 方法：
```java
// EmotionService.java

private static final String SYSTEM_PROMPT = """
你是情感分类器。从下面的标签中选出最符合用户这句话的一个，只输出英文标签，不要输出任何别的内容。
normal：平常、陈述、闲聊
sorry：向对方道歉、请求原谅，重点是"对不起你"
sad：难过、悲痛、自责、后悔，重点是自己的痛苦，不一定在向谁道歉
happy：开心、兴奋
shenqing：深情、告白、真挚地表达感情

例子：
对不起，我错了，你就原谅我嘛 → sorry
都是我的错，如果不是我，他根本不会出事 → sad
他再也不会回来了 → sad
""";

public String classify(String text) {
	ChatRequest request = new ChatRequest("deepseek-chat", List.of(
						  new Message("system", SYSTEM_PROMPT),
						  new Message("user", text)
	));
	ChatResponse response = restClient.post()
									  .uri("/chat/completions")
									  .header("Authorization", "Bearer " + apiKey)
									  .contentType(MediaType.APPLICATION_JSON)
									  .body(request)
									  .retrieve()
									  .body(ChatResponse.class);
	String emotion = response.choices().get(0).message().content().trim();
	System.out.println("大模型判断：" + text + " → " + emotion);
	return emotion;
}
```

这个方法先接收 TtsController 传进来的文本，然后调用 deepseek 的接口，把提示词什么的传进去，最后返回 emotion。

得到 emotion 之后，TtsController 就把它传入 TtsService 的方法中（`byte[] wav = ttsService.synthesize(text, emotion);`），去调用 GSV 来生成音频：
```java
// TtsService.java

@Service
public class TtsService {
// 一段参考音频 = 文件路径 + 音频里说的原文 + 原文的语言
	record RefAudio(String path, String text, String lang) {}
	private final RestClient restClient;

// 情感 → 参考音频（以后这张表会换成数据库查询）
	private final Map<String, RefAudio> refs = Map.of(
		"normal", new RefAudio(
				"参考音频路径",
				"参考音频文本",
				"参考音频语言")
	);
	
	public TtsService(@Value("${gsv.base-url}") String baseUrl) {
		this.restClient = RestClient.create(baseUrl);
	}

	public byte[] synthesize(String text, String emotion) {
// 表里没有这个情感，就退回 normal
		RefAudio ref = refs.getOrDefault(emotion, refs.get("normal"));
		System.out.println("emotion=" + emotion + " → 用的参考音频：" + ref.path());
		return restClient.get()
						 .uri(uriBuilder -> uriBuilder
						 .path("/tts")
						 .queryParam("text", "{text}")
						 .queryParam("text_lang", "zh")
						 .queryParam("ref_audio_path", "{ref}")
						 .queryParam("prompt_lang", ref.lang())
						 .queryParam("prompt_text", "{prompt}")
						 .build(text, ref.path(), ref.text()))
						 .retrieve()
						 .body(byte[].class);
	}
}
```

8080 端口就会向9880 端口发送请求，并带上“text”、“text_lang”等等接口参数。