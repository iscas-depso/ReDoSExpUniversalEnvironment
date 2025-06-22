package cn.ac.ios;

import cn.ac.ios.Bean.ReDoSBean;
import cn.ac.ios.Bean.AttackBean;
import cn.ac.ios.Bean.Attack;
import cn.ac.ios.Bean.Output;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import org.apache.commons.io.FileUtils;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

/**
 * Command-line interface for ReDoSHunter
 * Usage: java -jar ReDoSHunter.jar <input_dir> <input_file> <output_dir>
 */
public class Main {
    public static final String ATTACK_MODEL_SINGLE = "s";
    public static final String ATTACK_MODEL_MULTI = "m";

    public static void main(String[] args) {
        if (args.length != 3) {
            System.err.println("Usage: java -jar ReDoSHunter.jar <input_dir> <input_file> <output_dir>");
            System.exit(1);
        }

        String inputDir = args[0];
        String inputFile = args[1];
        String outputDir = args[2];

        try {
            // Read input file
            File file = new File(inputDir, inputFile);
            List<String> lines = FileUtils.readLines(file, "utf-8");
            
            if (lines.isEmpty()) {
                System.err.println("Input file is empty");
                System.exit(1);
            }

            // Process each regex (usually just one)
            List<Output> outputs = new ArrayList<>();
            
            for (int i = 0; i < lines.size(); i++) {
                String regex = lines.get(i).trim();
                if (regex.isEmpty()) continue;
                
                // Check for ReDoS
                ReDoSBean checkResult = ReDoSMain.checkReDoS(regex, i + 1, "11111", "java");
                
                // Validate with attack strings
                ReDoSBean validatedResult = ReDoSMain.validateReDoS(checkResult, ATTACK_MODEL_SINGLE, "java");
                
                // Convert to output format
                ArrayList<Attack> attackList = new ArrayList<>();
                for (AttackBean attackBean : validatedResult.getAttackBeanList()) {
                    Attack attack = new Attack(
                        attackBean.getPrefix(),
                        attackBean.getInfix(), 
                        attackBean.getSuffix(),
                        attackBean.getType(),
                        attackBean.getPatternType(),
                        attackBean.getRepeatTimes()  // Add repeat times
                    );
                    attackList.add(attack);
                }
                
                Output output = new Output(validatedResult.getRegexID(), validatedResult.getRegex(), attackList);
                outputs.add(output);
            }

            // Write JSON output
            Gson gson = new GsonBuilder().setPrettyPrinting().create();
            String json = gson.toJson(outputs);
            
            // Create output file
            String outputFileName = inputFile.replace(".txt", "_result.json");
            File outputFile = new File(outputDir, outputFileName);
            FileUtils.write(outputFile, json, "utf-8");
            
            System.out.println("ReDoSHunter analysis completed. Output written to: " + outputFile.getAbsolutePath());
            
        } catch (Exception e) {
            System.err.println("Error processing regex: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
}
