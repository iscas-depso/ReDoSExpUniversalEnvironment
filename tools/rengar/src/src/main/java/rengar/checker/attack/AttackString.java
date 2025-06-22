package rengar.checker.attack;

import rengar.checker.pattern.DisturbType;
import rengar.parser.charutil.*;
import java.util.Arrays;

public class AttackString {
    private int[] prefix;
    private int[] attack;
    private int n;
    private int[] postfix;
    private DisturbType disturbType = new DisturbType();

    public void setDisturbType(DisturbType type) {
        this.disturbType = type;
    }

    public DisturbType getDisturbType() {
        return this.disturbType;
    }

    public void setPrefix(int[] prefix) {
        this.prefix = prefix;
    }

    public void setAttack(int[] attack, int n) {
        this.attack = attack;
        this.n = n;
    }

    public void setAttack(int[] attack) {
        this.attack = attack;
    }

    public void setN(int n) {
        this.n = n;
    }

    public void setPostfix(int[] postfix) {
        this.postfix = postfix;
    }

    // Public getter methods for accessing attack string components
    public int[] getPrefix() {
        return this.prefix;
    }

    public int[] getAttack() {
        return this.attack;
    }

    public int getN() {
        return this.n;
    }

    public int[] getPostfix() {
        return this.postfix;
    }

    public String genStr() {
        StringBuilder sb = new StringBuilder();
        sb.append(CharUtil.toString(prefix));
        sb.append(CharUtil.toString(attack).repeat(n));
        sb.append(CharUtil.toString(postfix));
        return sb.toString();
    }

    public String genReadableStr() {
        return String.format("\"%s\" + \"%s\" * %d + \"%s\"",
                CharUtil.toPrintableString(prefix),
                CharUtil.toPrintableString(attack), n,
                CharUtil.toPrintableString(postfix));
    }

    public String genRawStr() {
        StringBuilder sb = new StringBuilder();
        sb.append(CharUtil.toString(prefix));
        // for (int i = 0; i < n; i++) {
        //     sb.append(CharUtil.toString(attack));
        // }
        // compute how many times need to repeat the attack string
        // target length of prefix + attack * repeat_times + postfix = 100KB
        // int repeat_times = (100 * 1024 - prefix.length - postfix.length) / attack.length;
        int repeat_times = (1024 * 1024 - prefix.length - postfix.length) / attack.length;
        sb.append(CharUtil.toString(attack).repeat(repeat_times));
        sb.append(CharUtil.toString(postfix));
        // System.out.println(sb.toString());
        return sb.toString();
    }

    @Override
    public boolean equals(Object o) {
        if (this == o)
            return true;
        if (o instanceof AttackString as) {
            return Arrays.equals(this.prefix, as.prefix)
                    && Arrays.equals(this.attack, as.attack)
                    && Arrays.equals(this.postfix, as.postfix)
                    && this.n == as.n;
        }
        return false;
    }

    @Override
    public int hashCode() {
        return Arrays.hashCode(prefix) ^ Arrays.hashCode(attack) ^ Arrays.hashCode(postfix) ^ n;
    }
}
