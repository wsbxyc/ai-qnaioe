package test;
import dev.langchain4j.model.dashscope.QwenChatModel;
public class Test {
    public static void main(String[] args) {
        QwenChatModel.Builder b = QwenChatModel.builder();
        java.lang.reflect.Method[] methods = b.getClass().getMethods();
        for(java.lang.reflect.Method m : methods) {
            System.out.println(m.getName());
        }
    }
}
