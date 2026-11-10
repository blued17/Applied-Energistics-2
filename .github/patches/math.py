# ===== Math expressions in number fields (like 64*4 or 100/4+2), as in newer AE2 versions =====
base = 'src/main/java/appeng/client/gui/'

open(base + 'MathExpressionParser.java', 'w').write('''package appeng.client.gui;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.text.DecimalFormat;
import java.text.ParsePosition;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Stack;

/**
 * Evaluates simple math expressions with + - * / ^ and parentheses.
 */
public class MathExpressionParser {
    private static final BigDecimal THIRTY = BigDecimal.valueOf(30);
    private static final BigDecimal ONE_BILLION = BigDecimal.valueOf(1e9);

    public static Optional<BigDecimal> parse(String expression, DecimalFormat decimalFormat) {
        // Parse using the Shunting Yard Algorithm

        List<Object> output = new ArrayList<>();
        Stack<Character> operatorStack = new Stack<>();
        boolean wasNumberOrRightBracket = false;

        for (int i = 0; i < expression.length();) {
            if (Character.isWhitespace(expression.charAt(i))) {
                i++;
                continue;
            }

            if (!wasNumberOrRightBracket && expression.charAt(i) != '-') {
                ParsePosition position = new ParsePosition(i);
                Number parsedNumber = decimalFormat.parse(expression, position);
                if (position.getErrorIndex() == -1) { // no error
                    if (!(parsedNumber instanceof BigDecimal)) {
                        // NaN or infinity
                        return Optional.empty();
                    }
                    output.add((BigDecimal) parsedNumber);
                    i = position.getIndex();
                    wasNumberOrRightBracket = true;
                    continue;
                }
            }

            char currentOperator = expression.charAt(i);
            if (currentOperator == '-' && !wasNumberOrRightBracket) {
                currentOperator = 'u'; // unitary minus
            }

            wasNumberOrRightBracket = false;

            switch (currentOperator) {
                case '(':
                case 'u':
                    operatorStack.push(currentOperator);
                    break;
                case ')':
                    while (true) {
                        if (operatorStack.isEmpty()) {
                            return Optional.empty(); // mismatched parenthesis
                        }
                        char operator = operatorStack.pop();
                        if (operator == '(') {
                            break;
                        } else {
                            output.add(operator);
                        }
                    }
                    wasNumberOrRightBracket = true;
                    break;
                case '+':
                case '-':
                case '*':
                case '/':
                case '^':
                    while (!operatorStack.isEmpty()) {
                        char operator = operatorStack.peek();
                        if (operator != '(' && precedenceCheck(operator, currentOperator)) {
                            operatorStack.pop();
                            output.add(operator);
                        } else {
                            break;
                        }
                    }
                    operatorStack.push(currentOperator);
                    break;
                default:
                    return Optional.empty();
            }
            i++;
        }

        while (!operatorStack.isEmpty()) {
            output.add(operatorStack.pop());
        }

        Stack<BigDecimal> number = new Stack<>();

        for (Object object : output) {
            if (object instanceof BigDecimal) {
                number.push((BigDecimal) object);
            } else {
                char currentOperator = (Character) object;
                if (currentOperator != 'u') {
                    if (number.size() < 2) {
                        return Optional.empty();
                    } else {
                        BigDecimal right = number.pop();
                        BigDecimal left = number.pop();
                        switch (currentOperator) {
                            case '+':
                                number.push(right.add(left));
                                break;
                            case '*':
                                number.push(right.multiply(left));
                                break;
                            case '-':
                                number.push(left.subtract(right));
                                break;
                            case '/':
                                if (right.compareTo(BigDecimal.ZERO) == 0) {
                                    return Optional.empty(); // division by zero
                                } else {
                                    number.push(left.divide(right, 8, RoundingMode.FLOOR));
                                }
                                break;
                            case '^':
                                right = right.stripTrailingZeros();
                                // if has a decimal part or is smaller than 0 -> nope
                                if (right.scale() > 0 || right.compareTo(BigDecimal.ZERO) < 0) {
                                    return Optional.empty();
                                }
                                // limit exponent to 30
                                if (right.compareTo(THIRTY) > 0) {
                                    return Optional.empty(); // exponent too big
                                }
                                // limit base number to 1e9
                                if (left.compareTo(ONE_BILLION) > 0) {
                                    return Optional.empty(); // base number too big
                                }
                                number.push(left.pow(right.intValueExact()));
                                break;
                            default:
                                return Optional.empty(); // should not have any remaining parenthesis
                        }
                    }
                } else {
                    if (number.isEmpty()) {
                        return Optional.empty();
                    } else {
                        number.push(number.pop().negate());
                    }
                }
            }
        }

        if (number.size() != 1) {
            return Optional.empty();
        } else {
            return Optional.of(number.pop().stripTrailingZeros());
        }
    }

    private static int getPrecedence(char operator) {
        switch (operator) {
            case '^':
                return -1;
            case 'u':
                return 0;
            case '/':
            case '*':
                return 1;
            case '+':
            case '-':
                return 2;
            default:
                throw new IllegalArgumentException("Invalid Operator : " + operator);
        }
    }

    private static boolean precedenceCheck(char first, char second) {
        return getPrecedence(first) <= getPrecedence(second);
    }

}
''')

path = base + 'implementations/NumberEntryWidget.java'
s = open(path).read()
if 'MathExpressionParser' not in s:
    def rep(old, new):
        global s
        assert s.count(old) == 1, 'anchor not found exactly once: ' + old[:80]
        s = s.replace(old, new)

    rep('package appeng.client.gui.implementations;\n',
        'package appeng.client.gui.implementations;\n\n'
        'import java.math.BigDecimal;\n'
        'import java.text.DecimalFormat;\n'
        'import java.text.DecimalFormatSymbols;\n'
        'import java.util.Optional;\n\n'
        'import appeng.client.gui.MathExpressionParser;\n')

    rep('    private final NumberEntryType type;\n',
        '    private final NumberEntryType type;\n'
        '    private final DecimalFormat decimalFormat = createDecimalFormat();\n')

    rep('        this.textField.setMaxStringLength(16);\n',
        '        this.textField.setMaxStringLength(64);\n')

    # getIntValue
    start = s.index('    public OptionalInt getIntValue() {')
    end = s.index('    public OptionalLong getLongValue() {')
    # keep the javadoc of getLongValue: find the start of that javadoc
    end_doc = s.rfind('    /**', start, end)
    s = s[:start] + '''    public OptionalInt getIntValue() {
        OptionalLong value = getLongValue();
        if (value.isPresent() && value.getAsLong() <= Integer.MAX_VALUE && value.getAsLong() >= Integer.MIN_VALUE) {
            return OptionalInt.of((int) value.getAsLong());
        }
        return OptionalInt.empty();
    }

''' + s[end_doc:]

    # getLongValue
    start = s.index('    public OptionalLong getLongValue() {')
    end = s.index('    public void setValue(long value) {')
    s = s[:start] + '''    public OptionalLong getLongValue() {
        Optional<BigDecimal> value = evaluate();
        if (!value.isPresent() || value.get().scale() > 0) {
            return OptionalLong.empty();
        }
        try {
            long result = value.get().longValueExact();
            if (result < minValue) {
                return OptionalLong.empty();
            }
            return OptionalLong.of(result);
        } catch (ArithmeticException ignored) {
            return OptionalLong.empty();
        }
    }

    private static DecimalFormat createDecimalFormat() {
        DecimalFormat format = new DecimalFormat("#.######", new DecimalFormatSymbols());
        format.setParseBigDecimal(true);
        format.setNegativePrefix("-");
        return format;
    }

    /**
     * Evaluates the text, which can be a plain number or a math expression (x is accepted as multiplication).
     */
    private Optional<BigDecimal> evaluate() {
        String text = textField.getText().trim().replace('x', '*').replace('X', '*').replace('\\u00d7', '*');
        if (text.isEmpty()) {
            return Optional.empty();
        }
        return MathExpressionParser.parse(text, decimalFormat);
    }

    private boolean isPlainNumber() {
        return textField.getText().trim().matches("-?\\\\d+");
    }

''' + s[end:]

    # validate
    start = s.index('    private void validate() {')
    end = s.index('    private ITextComponent makeLabel(')
    s = s[:start] + '''    private void validate() {
        List<ITextComponent> validationErrors = new ArrayList<>();
        List<ITextComponent> infoMessages = new ArrayList<>();

        Optional<BigDecimal> value = evaluate();
        if (value.isPresent()) {
            BigDecimal result = value.get();
            if (result.scale() > 0) {
                validationErrors.add(INVALID_NUMBER);
            } else if (result.compareTo(BigDecimal.valueOf(minValue)) < 0) {
                validationErrors.add(new TranslationTextComponent(NUMBER_LESS_THAN_MIN_VALUE, minValue));
            } else if (result.compareTo(BigDecimal.valueOf(Long.MAX_VALUE)) > 0) {
                validationErrors.add(INVALID_NUMBER);
            } else if (!isPlainNumber()) {
                // A math expression: show what it evaluates to
                infoMessages.add(new StringTextComponent("= " + decimalFormat.format(result)));
            }
        } else {
            validationErrors.add(INVALID_NUMBER);
        }

        boolean valid = validationErrors.isEmpty();
        this.textField.setTextColor(valid ? TEXT_COLOR_NORMAL : TEXT_COLOR_ERROR);
        if (this.validationIcon != null) {
            this.validationIcon.setValid(valid);
            this.validationIcon.setTooltip(valid ? infoMessages : validationErrors);
        }
    }

''' + s[end:]
    open(path, 'w').write(s)
print('math applied')
