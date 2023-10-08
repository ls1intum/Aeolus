plugins {
    id("java")
    id("org.jsonschema2pojo") version "1.2.1"
    id("com.github.johnrengelman.shadow") version "7.1.0"
}

configure <org.jsonschema2pojo.gradle.JsonSchemaExtension> {
    sourceFiles = mutableListOf(
        file("../schemas/v0.0.1/schemas/definitions.json"),
        file("../schemas/v0.0.1/schemas/environment.json")
    )
    includeAdditionalProperties = false
    includeConstructors = true
    targetPackage = "de.tum.cit.ase.generated"
    targetDirectory = file("src/main/java/")
    initializeCollections = true
    includeConstructors = true
    generateBuilders = true
}

group = "de.tum.cit.ase"
version = "0.0.1"

repositories {
    mavenCentral()
}

dependencies {
//    implementation("com.fasterxml.jackson.core:jackson-annotations:2.15.2")
    implementation("com.atlassian.bamboo:bamboo-specs:9.3.3")
    // https://mvnrepository.com/artifact/org.jsonschema2pojo/jsonschema2pojo-core
    implementation("org.jsonschema2pojo:jsonschema2pojo-core:1.2.1")
    // https://mvnrepository.com/artifact/com.squareup.okhttp3/okhttp
    implementation("com.squareup.okhttp3:okhttp:4.11.0")

//    implementation("org.yaml:snakeyaml:2.2")
    implementation("com.google.code.gson:gson:2.10.1")
    testImplementation(platform("org.junit:junit-bom:5.9.1"))
    testImplementation("org.junit.jupiter:junit-jupiter")
}

tasks.test {
    useJUnitPlatform()
}

tasks.withType<Jar> {
    manifest {
        attributes["Main-Class"] = "de.tum.cit.ase.Main"
    }
}