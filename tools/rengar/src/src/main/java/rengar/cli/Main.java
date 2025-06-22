package rengar.cli;

import rengar.checker.StaticPipeline;
import rengar.checker.attack.AttackString;
import rengar.checker.pattern.DisturbFreePattern;
import com.alibaba.fastjson.JSONObject;
import rengar.config.GlobalConfig;
import org.apache.commons.cli.*;
import rengar.parser.RegexParser;
import rengar.util.Pair;
import rengar.parser.charutil.CharUtil;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.LinkedList;
import java.util.List;
import java.io.File;

public class Main {
    private final static Options options = new Options();
    private final static CommandLineParser cliParser = new DefaultParser();
    private final static HelpFormatter helpFormatter = new HelpFormatter();

    public static void main(String[] args) throws IOException {
        CommandLine cli = initCommandArgument(args);
        if (cli.hasOption("disablePreprocess"))
            GlobalConfig.option.disablePreprocess();
        if (cli.hasOption("weakPatternCheck"))
            GlobalConfig.option.weakPatternCheck();
        if (cli.hasOption("ingoreDisturbance"))
            GlobalConfig.option.ignoreDisturbance();
        if (cli.hasOption("multiple"))
            GlobalConfig.option.multipleVulnerabilityMode();
        if (cli.hasOption("quiet"))
            GlobalConfig.option.quiet();
        if (cli.hasOption("staticTimeout")) {
            int timeout = Integer.parseInt(cli.getOptionValue("staticTimeout"));
            GlobalConfig.option.setStaticTimeout(timeout);
        }
        if (cli.hasOption("totalTimeout")) {
            int timeout = Integer.parseInt(cli.getOptionValue("totalTimeout"));
            GlobalConfig.option.setTotalTimeout(timeout);
        }
        if (cli.hasOption("threadNumber")) {
            int number = Integer.parseInt(cli.getOptionValue("threadNumber"));
            GlobalConfig.option.setThreadNumber(number);
        }
        if (cli.hasOption("single")) {
            String b64regex = cli.getOptionValue("single");
            int id = Integer.parseInt(cli.getOptionValue("id"));
            JSONObject jsonObject = Batch.handleSingleRegex(id, b64regex, true);
            System.out.println(jsonObject);
        } else {
            helpFormatter.printHelp("Rengar", options);
        }
        GlobalConfig.executor.shutdownNow();
    }

    private static CommandLine initCommandArgument(String[] args) {
        Option opt2 = new Option(
                "d",
                "disablePreprocess",
                false,
                "disable regex preprocess"
        );
        opt2.setRequired(false);
        Option opt3 = new Option(
                "w",
                "weakPatternCheck",
                false,
                "weak ReDoS pattern check"
        );
        opt3.setRequired(false);
        Option opt4 = new Option(
                "i",
                "ingoreDisturbance",
                false,
                "ingore disturbance"
        );
        opt4.setRequired(false);
        Option opt5 = new Option(
                "m",
                "multiple",
                false,
                "multiple vulnerability mode"
        );
        opt5.setRequired(false);
        Option opt6 = new Option(
                "q",
                "quiet",
                false,
                "less output information"
        );
        opt6.setRequired(false);
        Option opt7 = new Option(
                "s",
                "single",
                true,
                "base64ed regex"
        );
        opt7.setRequired(false);
        Option opt8 = new Option(
                "t",
                "id",
                true,
                "id"
        );
        opt8.setRequired(false);
        Option opt9 = new Option(
                "st",
                "staticTimeout",
                true,
                "static checker timeout"
        );
        opt9.setRequired(false);
        Option opt10 = new Option(
                "tt",
                "totalTimeout",
                true,
                "total timeout"
        );
        opt10.setRequired(false);
        Option opt11 = new Option(
                "tn",
                "threadNumber",
                true,
                "thread number"
        );
        opt11.setRequired(false);
        options.addOption(opt2);
        options.addOption(opt3);
        options.addOption(opt4);
        options.addOption(opt5);
        options.addOption(opt6);
        options.addOption(opt7);
        options.addOption(opt8);
        options.addOption(opt9);
        options.addOption(opt10);
        options.addOption(opt11);
        try {
            return cliParser.parse(options, args);
        } catch (ParseException e) {
            helpFormatter.printHelp("Rengar", options);
            System.exit(0);
        }
        return null;
    }

    static class Batch {
        public static JSONObject handleSingleRegex(int id, String patternStr) {
            return handleSingleRegex(id, patternStr, false);
        }

        public static JSONObject handleSingleRegex(int id, String patternStr, boolean base64) {
            JSONObject jsonObject = new JSONObject();
            jsonObject.put("ID", id);
            String b64Regex;
            if (base64) {
                b64Regex = patternStr;
                patternStr = b64decode(patternStr);
            } else {
                b64Regex = b64encode(patternStr);
            }
            jsonObject.put("Regex", b64Regex);
            StaticPipeline.Result result = StaticPipeline.runWithTimeOut(
                    patternStr,
                    RegexParser.Language.Java,
                    GlobalConfig.option.isMultipleVulnerabilityMode()
            );
            if (result == null) {
                jsonObject.put("Status", "Timeout");
            } else {
                switch (result.state) {
                    case InternalBug -> jsonObject.put("Status", "InternalBug");
                    case SyntaxError -> jsonObject.put("Status", "SyntaxError");
                    case Normal -> jsonObject.put("Status", "Safe");
                    case Vulnerable -> {
                        File directory = new File("AttackString");
                        if (!directory.exists()) {
                            if (directory.mkdir()) {
                                System.out.println("AttackString文件夹已创建成功");
                            } else {
                                System.out.println("AttackString文件夹创建失败");
                            }
                        } else {
                            System.out.println("AttackString文件夹已存在");
                        }
                        jsonObject.put("Status", "Vulnerable");
                        List<JSONObject> patternList = new LinkedList<>();
                        for (Pair<DisturbFreePattern, AttackString> pair : result.attacks) {
                            DisturbFreePattern pattern = pair.getLeft();
                            AttackString as = pair.getRight();
                            JSONObject patternObj = new JSONObject();
                            patternObj.put("Type", pattern.getType());
                            // String tmp = as.genReadableStr();
                            patternObj.put("AttackString", b64encode(as.genReadableStr()));
                            
                            // Add the attack string components
                            String prefix = CharUtil.toString(as.getPrefix());
                            String infix = CharUtil.toString(as.getAttack());
                            String suffix = CharUtil.toString(as.getPostfix());
                            int repeatTimes = as.getN();
                            
                            patternObj.put("Prefix", b64encode(prefix));
                            patternObj.put("Infix", b64encode(infix));
                            patternObj.put("Suffix", b64encode(suffix));
                            patternObj.put("RecommendedRepeatTimes", repeatTimes);
                            
                            patternList.add(patternObj);
                            // // 将串通过as.genRawStr()生成的字符串输出到AttackingString/id.txt文件中
                            // String attackStr = as.genRawStr();
                            // String attackStrPath = "AttackString/" + id + ".txt";
                            // try {
                            //     File file = new File(attackStrPath);
                            //     if (!file.exists()) {
                            //         if (file.createNewFile()) {
                            //             System.out.println("AttackString文件已创建成功");
                            //         } else {
                            //             System.out.println("AttackString文件创建失败");
                            //         }
                            //     } else {
                            //         System.out.println("AttackString文件已存在");
                            //     }
                            //     java.io.FileWriter fileWriter = new java.io.FileWriter(file);
                            //     fileWriter.write(attackStr);
                            //     fileWriter.close();
                            // } catch (IOException e) {
                            //     e.printStackTrace();
                            // }
                            // jump out of the loop
                            break;
                        }
                        jsonObject.put("Details", patternList);
                        jsonObject.put("DisturbType", result.disturbType.getTypes());
                    }
                }
            }
            return jsonObject;
        }

        private static String b64encode(String str) {
            return new String(
                    Base64.getEncoder().encode(str.getBytes(StandardCharsets.UTF_8)),
                    StandardCharsets.UTF_8
            );
        }

        private static String b64decode(String str) {
            return new String(
                    Base64.getDecoder().decode(str.getBytes(StandardCharsets.UTF_8)),
                    StandardCharsets.UTF_8
            );
        }
    }
}