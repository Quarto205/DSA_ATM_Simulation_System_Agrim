import java.io.*;
import java.math.BigDecimal;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.function.Predicate;
import java.util.stream.Collectors;
public class ATMSimulation {

    public static void main(String[] args) {
        System.out.println("[*] Starting ATM Simulation System...");
        String dataDir = "data";
        new File(dataDir).mkdirs();
        Repository<Account> accountRepo = new JsonRepository<>(dataDir + "/accounts.json", Account::fromJson);
        Repository<Card> cardRepo = new JsonRepository<>(dataDir + "/cards.json", Card::fromJson);
        Repository<Transaction> txRepo = new JsonRepository<>(dataDir + "/transactions.json", Transaction::fromJson);
        Repository<Admin> adminRepo = new JsonRepository<>(dataDir + "/admin.json", Admin::fromJson);
        Repository<ATM> atmRepo = new JsonRepository<>(dataDir + "/atm.json", ATM::fromJson);
        Repository<Session> sessionRepo = new JsonRepository<>(dataDir + "/sessions.json", Session::fromJson);
        seedInitialData(adminRepo, accountRepo, cardRepo);
        CashService cashService = new CashService(atmRepo);
        AuthenticationService authService = new AuthenticationService(cardRepo, adminRepo, sessionRepo);
        BankService bankService = new BankService(accountRepo, txRepo, cashService);
        AdminService adminService = new AdminService(cardRepo, accountRepo, txRepo, cashService);
        ATMCLI cli = new ATMCLI(authService, bankService, adminService);
        cli.run();
    }

    private static void seedInitialData(Repository<Admin> adminRepo, Repository<Account> accountRepo, Repository<Card> cardRepo) {
        if (adminRepo.getAll().isEmpty()) {
            Admin admin = new Admin("admin", AuthenticationService.hashPin("0000"));
            adminRepo.save(admin, admin.getAdminId().toString());
            System.out.println("[*] Seeded default admin (User: admin, PIN: 0000)");
        }

        if (accountRepo.getAll().isEmpty()) {
            Account acc1 = new Account("1001234567");
            accountRepo.save(acc1, acc1.getAccountId().toString());

            Card card = new Card("4000123456789010", AuthenticationService.hashPin("1234"), acc1.getAccountId());
            cardRepo.save(card, card.getCardId().toString());

            Account acc2 = new Account("1009876543");
            accountRepo.save(acc2, acc2.getAccountId().toString());

            System.out.println("[*] Seeded default customer (Card: 4000123456789010, PIN: 1234)");
        }
    }
}
class ATMException extends RuntimeException {
    public ATMException(String message) { super(message); }
}
class InsufficientFundsException extends ATMException {
    public InsufficientFundsException(String message) { super(message); }
}
class AccountLockedException extends ATMException {
    public AccountLockedException(String message) { super(message); }
}
interface JsonSerializable {
    String toJson();
}
class Account implements JsonSerializable {
    private UUID accountId;
    private String accountNumber;
    private BigDecimal balance;

    public Account(String accountNumber) {
        this.accountId = UUID.randomUUID();
        this.accountNumber = accountNumber;
        this.balance = BigDecimal.ZERO;
    }

    private Account(UUID id, String accNum, BigDecimal bal) {
        this.accountId = id;
        this.accountNumber = accNum;
        this.balance = bal;
    }

    public void deposit(BigDecimal amount) {
        if (amount.compareTo(BigDecimal.ZERO) <= 0) throw new ATMException("Deposit must be positive.");
        this.balance = this.balance.add(amount);
    }

    public void withdraw(BigDecimal amount) {
        if (amount.compareTo(BigDecimal.ZERO) <= 0) throw new ATMException("Withdrawal must be positive.");
        if (amount.compareTo(this.balance) > 0) throw new InsufficientFundsException("Insufficient funds.");
        this.balance = this.balance.subtract(amount);
    }

    public UUID getAccountId() { return accountId; }
    public String getAccountNumber() { return accountNumber; }
    public BigDecimal getBalance() { return balance; }

    @Override
    public String toJson() {
        return String.format("{\"accountId\":\"%s\",\"accountNumber\":\"%s\",\"balance\":\"%s\"}", accountId, accountNumber, balance);
    }

    public static Account fromJson(String json) {
        Map<String, String> map = SimpleJsonParser.parse(json);
        return new Account(UUID.fromString(map.get("accountId")), map.get("accountNumber"), new BigDecimal(map.get("balance")));
    }
}

class Card implements JsonSerializable {
    private UUID cardId;
    private String cardNumber;
    private String pinHash;
    private UUID accountId;
    private int failedLoginAttempts;
    private boolean isLocked;

    public Card(String cardNumber, String pinHash, UUID accountId) {
        this.cardId = UUID.randomUUID();
        this.cardNumber = cardNumber;
        this.pinHash = pinHash;
        this.accountId = accountId;
        this.failedLoginAttempts = 0;
        this.isLocked = false;
    }

    private Card(UUID id, String cNum, String pin, UUID accId, int fails, boolean locked) {
        this.cardId = id;
        this.cardNumber = cNum;
        this.pinHash = pin;
        this.accountId = accId;
        this.failedLoginAttempts = fails;
        this.isLocked = locked;
    }

    public void recordFailedAttempt() {
        failedLoginAttempts++;
        if (failedLoginAttempts >= 3) isLocked = true;
    }

    public void resetFailedAttempts() {
        failedLoginAttempts = 0;
        isLocked = false;
    }

    public void checkAccess() {
        if (isLocked) throw new AccountLockedException("Card is locked due to too many failed attempts.");
    }

    public UUID getCardId() { return cardId; }
    public String getCardNumber() { return cardNumber; }
    public String getPinHash() { return pinHash; }
    public UUID getAccountId() { return accountId; }
    public boolean isLocked() { return isLocked; }

    @Override
    public String toJson() {
        return String.format("{\"cardId\":\"%s\",\"cardNumber\":\"%s\",\"pinHash\":\"%s\",\"accountId\":\"%s\",\"failedLoginAttempts\":\"%d\",\"isLocked\":\"%b\"}",
                cardId, cardNumber, pinHash, accountId, failedLoginAttempts, isLocked);
    }

    public static Card fromJson(String json) {
        Map<String, String> map = SimpleJsonParser.parse(json);
        return new Card(UUID.fromString(map.get("cardId")), map.get("cardNumber"), map.get("pinHash"),
                UUID.fromString(map.get("accountId")), Integer.parseInt(map.get("failedLoginAttempts")), Boolean.parseBoolean(map.get("isLocked")));
    }
}

class Transaction implements JsonSerializable {
    private UUID transactionId;
    private UUID accountId;
    private String type;
    private BigDecimal amount;
    private LocalDateTime timestamp;

    public Transaction(UUID accountId, String type, BigDecimal amount) {
        this.transactionId = UUID.randomUUID();
        this.accountId = accountId;
        this.type = type;
        this.amount = amount;
        this.timestamp = LocalDateTime.now();
    }

    private Transaction(UUID txId, UUID accId, String type, BigDecimal amt, LocalDateTime ts) {
        this.transactionId = txId;
        this.accountId = accId;
        this.type = type;
        this.amount = amt;
        this.timestamp = ts;
    }

    public UUID getAccountId() { return accountId; }
    public String getType() { return type; }
    public BigDecimal getAmount() { return amount; }
    public LocalDateTime getTimestamp() { return timestamp; }

    @Override
    public String toJson() {
        return String.format("{\"transactionId\":\"%s\",\"accountId\":\"%s\",\"type\":\"%s\",\"amount\":\"%s\",\"timestamp\":\"%s\"}",
                transactionId, accountId, type, amount, timestamp.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
    }

    public static Transaction fromJson(String json) {
        Map<String, String> map = SimpleJsonParser.parse(json);
        return new Transaction(UUID.fromString(map.get("transactionId")), UUID.fromString(map.get("accountId")),
                map.get("type"), new BigDecimal(map.get("amount")), LocalDateTime.parse(map.get("timestamp"), DateTimeFormatter.ISO_LOCAL_DATE_TIME));
    }
}

class Admin implements JsonSerializable {
    private UUID adminId;
    private String username;
    private String pinHash;

    public Admin(String username, String pinHash) {
        this.adminId = UUID.randomUUID();
        this.username = username;
        this.pinHash = pinHash;
    }

    private Admin(UUID id, String user, String pin) {
        this.adminId = id; this.username = user; this.pinHash = pin;
    }

    public UUID getAdminId() { return adminId; }
    public String getUsername() { return username; }
    public String getPinHash() { return pinHash; }

    @Override
    public String toJson() {
        return String.format("{\"adminId\":\"%s\",\"username\":\"%s\",\"pinHash\":\"%s\"}", adminId, username, pinHash);
    }

    public static Admin fromJson(String json) {
        Map<String, String> map = SimpleJsonParser.parse(json);
        return new Admin(UUID.fromString(map.get("adminId")), map.get("username"), map.get("pinHash"));
    }
}

class ATM implements JsonSerializable {
    private UUID atmId;
    private Map<String, Integer> denominations;

    public ATM() {
        this.atmId = UUID.randomUUID();
        this.denominations = new HashMap<>();
        denominations.put("100", 50); denominations.put("50", 50);
        denominations.put("20", 100); denominations.put("10", 100);
    }

    private ATM(UUID id, Map<String, Integer> denoms) {
        this.atmId = id;
        this.denominations = denoms;
    }

    public UUID getAtmId() { return atmId; }
    public Map<String, Integer> getDenominations() { return denominations; }

    public BigDecimal getTotalCash() {
        return denominations.entrySet().stream()
                .map(e -> new BigDecimal(e.getKey()).multiply(new BigDecimal(e.getValue())))
                .reduce(BigDecimal.ZERO, BigDecimal::add);
    }

    public void dispense(BigDecimal amount) {
        if (amount.compareTo(getTotalCash()) > 0) throw new ATMException("ATM has insufficient physical cash.");
        // Simplified dispense logic for brevity. In a full system, we calculate exact bill mix here.
    }

    public void refill(Map<String, Integer> newDenoms) {
        newDenoms.forEach((k, v) -> denominations.put(k, denominations.getOrDefault(k, 0) + v));
    }

    @Override
    public String toJson() {
        String denomsStr = denominations.entrySet().stream()
                .map(e -> e.getKey() + ":" + e.getValue())
                .collect(Collectors.joining(";"));
        return String.format("{\"atmId\":\"%s\",\"denominations\":\"%s\"}", atmId, denomsStr);
    }

    public static ATM fromJson(String json) {
        Map<String, String> map = SimpleJsonParser.parse(json);
        Map<String, Integer> denoms = new HashMap<>();
        if (!map.get("denominations").isEmpty()) {
            for (String pair : map.get("denominations").split(";")) {
                String[] kv = pair.split(":");
                denoms.put(kv[0], Integer.parseInt(kv[1]));
            }
        }
        return new ATM(UUID.fromString(map.get("atmId")), denoms);
    }
}

class Session implements JsonSerializable {
    private UUID sessionId;
    private UUID userId;
    private String role;
    private boolean active;

    public Session(UUID userId, String role) {
        this.sessionId = UUID.randomUUID();
        this.userId = userId;
        this.role = role;
        this.active = true;
    }

    private Session(UUID sid, UUID uid, String role, boolean active) {
        this.sessionId = sid; this.userId = uid; this.role = role; this.active = active;
    }

    public UUID getUserId() { return userId; }
    public String getRole() { return role; }
    public void endSession() { this.active = false; }

    @Override
    public String toJson() {
        return String.format("{\"sessionId\":\"%s\",\"userId\":\"%s\",\"role\":\"%s\",\"active\":\"%b\"}", sessionId, userId, role, active);
    }

    public static Session fromJson(String json) {
        Map<String, String> map = SimpleJsonParser.parse(json);
        return new Session(UUID.fromString(map.get("sessionId")), UUID.fromString(map.get("userId")), map.get("role"), Boolean.parseBoolean(map.get("active")));
    }
}
interface Repository<T> {
    List<T> getAll();
    void save(T entity, String id);
    List<T> find(Predicate<T> predicate);
}

class JsonRepository<T extends JsonSerializable> implements Repository<T> {
    private final File file;
    private final java.util.function.Function<String, T> deserializer;
    private final Map<String, T> memoryStore = new HashMap<>();

    public JsonRepository(String filePath, java.util.function.Function<String, T> deserializer) {
        this.file = new File(filePath);
        this.deserializer = deserializer;
        loadFromFile();
    }

    private void loadFromFile() {
        if (!file.exists()) return;
        try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
            String line;
            while ((line = reader.readLine()) != null) {
                T obj = deserializer.apply(line);
                // We use a simplistic JSON approach where each line is a JSON object
                memoryStore.put(UUID.randomUUID().toString(), obj); // Internal map tracking
            }
        } catch (Exception e) { System.out.println("Error loading file: " + file.getName()); }
    }

    private void saveToFile() {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(file))) {
            for (T entity : memoryStore.values()) {
                writer.write(entity.toJson());
                writer.newLine();
            }
        } catch (IOException e) { throw new RuntimeException(e); }
    }

    @Override
    public List<T> getAll() {
        return new ArrayList<>(memoryStore.values());
    }

    @Override
    public void save(T entity, String id) {
        memoryStore.put(id, entity);
        saveToFile();
    }

    @Override
    public List<T> find(Predicate<T> predicate) {
        return memoryStore.values().stream().filter(predicate).collect(Collectors.toList());
    }
}
class SimpleJsonParser {
    public static Map<String, String> parse(String json) {
        Map<String, String> map = new HashMap<>();
        String content = json.substring(1, json.length() - 1); // remove { and }
        String[] pairs = content.split("\",\"");
        for (String pair : pairs) {
            String cleanPair = pair.replace("\"", "");
            String[] kv = cleanPair.split(":");
            if (kv.length == 2) map.put(kv[0], kv[1]);
        }
        return map;
    }
}
class CashService {
    private Repository<ATM> atmRepo;
    public CashService(Repository<ATM> atmRepo) { this.atmRepo = atmRepo; }

    public ATM getAtm() {
        List<ATM> atms = atmRepo.getAll();
        if (atms.isEmpty()) {
            ATM defaultAtm = new ATM();
            atmRepo.save(defaultAtm, defaultAtm.getAtmId().toString());
            return defaultAtm;
        }
        return atms.get(0);
    }
}

class AuthenticationService {
    private Repository<Card> cardRepo;
    private Repository<Admin> adminRepo;
    private Repository<Session> sessionRepo;

    public AuthenticationService(Repository<Card> cardRepo, Repository<Admin> adminRepo, Repository<Session> sessionRepo) {
        this.cardRepo = cardRepo; this.adminRepo = adminRepo; this.sessionRepo = sessionRepo;
    }

    public static String hashPin(String pin) {
        // Simplified hashing for demonstration
        return Integer.toHexString(pin.hashCode());
    }

    public Session loginCustomer(String cardNumber, String pin) {
        List<Card> cards = cardRepo.find(c -> c.getCardNumber().equals(cardNumber));
        if (cards.isEmpty()) throw new ATMException("Invalid card.");
        
        Card card = cards.get(0);
        card.checkAccess();

        if (!card.getPinHash().equals(hashPin(pin))) {
            card.recordFailedAttempt();
            cardRepo.save(card, card.getCardId().toString());
            if (card.isLocked()) throw new AccountLockedException("Card is locked.");
            throw new ATMException("Invalid PIN.");
        }

        card.resetFailedAttempts();
        cardRepo.save(card, card.getCardId().toString());
        
        Session session = new Session(card.getAccountId(), "CUSTOMER");
        sessionRepo.save(session, session.getUserId().toString());
        return session;
    }

    public Session loginAdmin(String username, String pin) {
        List<Admin> admins = adminRepo.find(a -> a.getUsername().equals(username));
        if (admins.isEmpty() || !admins.get(0).getPinHash().equals(hashPin(pin))) {
            throw new ATMException("Invalid admin credentials.");
        }
        Session session = new Session(admins.get(0).getAdminId(), "ADMIN");
        sessionRepo.save(session, session.getUserId().toString());
        return session;
    }
}

class BankService {
    private Repository<Account> accountRepo;
    private Repository<Transaction> txRepo;
    private CashService cashService;

    public BankService(Repository<Account> accountRepo, Repository<Transaction> txRepo, CashService cashService) {
        this.accountRepo = accountRepo; this.txRepo = txRepo; this.cashService = cashService;
    }

    private Account getAccount(UUID accountId) {
        return accountRepo.find(a -> a.getAccountId().equals(accountId)).get(0);
    }

    public BigDecimal getBalance(UUID accountId) {
        return getAccount(accountId).getBalance();
    }

    public void withdraw(UUID accountId, BigDecimal amount) {
        Account acc = getAccount(accountId);
        ATM atm = cashService.getAtm();
        
        atm.dispense(amount); // Checks ATM rules
        acc.withdraw(amount); // Checks Account rules
        
        Transaction tx = new Transaction(accountId, "WITHDRAWAL", amount);
        
        accountRepo.save(acc, acc.getAccountId().toString());
        txRepo.save(tx, tx.getAccountId().toString());
    }

    public void deposit(UUID accountId, BigDecimal amount) {
        Account acc = getAccount(accountId);
        acc.deposit(amount);
        Transaction tx = new Transaction(accountId, "DEPOSIT", amount);
        accountRepo.save(acc, acc.getAccountId().toString());
        txRepo.save(tx, tx.getAccountId().toString());
    }
}

class AdminService {
    private Repository<Card> cardRepo;
    private Repository<Account> accountRepo;
    private Repository<Transaction> txRepo;
    private CashService cashService;

    public AdminService(Repository<Card> cRepo, Repository<Account> aRepo, Repository<Transaction> tRepo, CashService cashService) {
        this.cardRepo = cRepo; this.accountRepo = aRepo; this.txRepo = tRepo; this.cashService = cashService;
    }

    public void unlockCard(String cardNumber) {
        List<Card> cards = cardRepo.find(c -> c.getCardNumber().equals(cardNumber));
        if (!cards.isEmpty()) {
            Card c = cards.get(0);
            c.resetFailedAttempts();
            cardRepo.save(c, c.getCardId().toString());
        }
    }
    
    public List<Account> getAllAccounts() { return accountRepo.getAll(); }

    public String[] openNewAccount(String pin, BigDecimal initialDeposit) {
        String accNum = "200" + String.format("%07d", new Random().nextInt(10000000));
        long random12 = Math.abs(new Random().nextLong()) % 1000000000000L;
        String cardNum = "4000" + String.format("%012d", random12);
        Account acc = new Account(accNum);
        if (initialDeposit.compareTo(BigDecimal.ZERO) > 0) {
            acc.deposit(initialDeposit);
            Transaction tx = new Transaction(acc.getAccountId(), "INITIAL_DEPOSIT", initialDeposit);
            txRepo.save(tx, tx.getAccountId().toString());
        }
        accountRepo.save(acc, acc.getAccountId().toString());
        Card card = new Card(cardNum, AuthenticationService.hashPin(pin), acc.getAccountId());
        cardRepo.save(card, card.getCardId().toString());

        return new String[]{accNum, cardNum};
    }
}
class ATMCLI {
    private AuthenticationService authService;
    private BankService bankService;
    private AdminService adminService;
    private Session currentSession;
    private Scanner scanner = new Scanner(System.in);

    public ATMCLI(AuthenticationService auth, BankService bank, AdminService admin) {
        this.authService = auth; this.bankService = bank; this.adminService = admin;
    }

    public void run() {
        while (true) {
            try {
                if (currentSession == null) showMainMenu();
                else if (currentSession.getRole().equals("CUSTOMER")) showCustomerMenu();
                else if (currentSession.getRole().equals("ADMIN")) showAdminMenu();
            } catch (Exception e) {
                System.out.println("\n[!] Error: " + e.getMessage());
            }
        }
    }

    private void showMainMenu() {
        System.out.println("\n=== ATM MAIN MENU ===");
        System.out.println("1. Insert Card (Customer Login)");
        System.out.println("2. Admin Login");
        System.out.println("3. Open New Account");
        System.out.println("4. Exit");
        System.out.print("Select: ");
        
        String choice = scanner.nextLine();
        if (choice.equals("1")) handleCustomerLogin();
        else if (choice.equals("2")) handleAdminLogin();
        else if (choice.equals("3")) handleOpenAccount();
        else if (choice.equals("4")) System.exit(0);
    }

    private void showCustomerMenu() {
        System.out.println("\n=== CUSTOMER MENU ===");
        System.out.println("1. Check Balance\n2. Withdraw\n3. Deposit\n4. Logout");
        System.out.print("Select: ");
        
        String choice = scanner.nextLine();
        if (choice.equals("1")) {
            System.out.println("Balance: $" + bankService.getBalance(currentSession.getUserId()));
        } else if (choice.equals("2")) {
            System.out.print("Amount to withdraw: $");
            bankService.withdraw(currentSession.getUserId(), new BigDecimal(scanner.nextLine()));
            System.out.println("Please take your cash.");
        } else if (choice.equals("3")) {
            System.out.print("Amount to deposit: $");
            bankService.deposit(currentSession.getUserId(), new BigDecimal(scanner.nextLine()));
            System.out.println("Cash deposited.");
        } else if (choice.equals("4")) {
            currentSession = null;
        }
    }

    private void showAdminMenu() {
        System.out.println("\n=== ADMIN MENU ===");
        System.out.println("1. View Accounts\n2. Unlock Card\n3. Logout");
        System.out.print("Select: ");
        
        String choice = scanner.nextLine();
        if (choice.equals("1")) {
            adminService.getAllAccounts().forEach(a -> 
                System.out.println("Account: " + a.getAccountNumber() + " | Bal: $" + a.getBalance())
            );
        } else if (choice.equals("2")) {
            System.out.print("Enter Card Number: ");
            adminService.unlockCard(scanner.nextLine());
            System.out.println("Card unlocked if it existed.");
        } else if (choice.equals("3")) {
            currentSession = null;
        }
    }

    private void handleCustomerLogin() {
        System.out.print("Enter Card Number: ");
        String card = scanner.nextLine();
        System.out.print("Enter PIN: ");
        String pin = scanner.nextLine();
        currentSession = authService.loginCustomer(card, pin);
        System.out.println("[*] Login Successful");
    }

    private void handleAdminLogin() {
        System.out.print("Enter Username: ");
        String user = scanner.nextLine();
        System.out.print("Enter PIN: ");
        String pin = scanner.nextLine();
        currentSession = authService.loginAdmin(user, pin);
        System.out.println("[*] Admin Login Successful");
    }

    private void handleOpenAccount() {
        System.out.println("\n=== OPEN NEW ACCOUNT ===");
        System.out.print("Set a 4-digit PIN: ");
        String pin = scanner.nextLine();
        System.out.print("Initial Deposit Amount: $");
        
        try {
            BigDecimal initialDeposit = new BigDecimal(scanner.nextLine());
            String[] details = adminService.openNewAccount(pin, initialDeposit);
            
            System.out.println("\n[*] Account Created Successfully!");
            System.out.println("    Account Number: " + details[0]);
            System.out.println("    Card Number:    " + details[1]);
            System.out.println("    (Please save your Card Number and PIN to login!)");
        } catch (Exception e) {
            System.out.println("[!] Failed to create account: " + e.getMessage());
        }
    }
}
