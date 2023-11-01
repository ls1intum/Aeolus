import com.github.jengelman.gradle.plugins.shadow.tasks.ShadowJar
import com.github.jengelman.gradle.plugins.shadow.transformers.PropertiesFileTransformer

plugins {
    java
    id("org.jsonschema2pojo") version "1.2.1"
    id("org.springframework.boot") version "3.1.5"
    id("com.github.johnrengelman.shadow") version "7.1.2"
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

java {
    sourceCompatibility = JavaVersion.VERSION_17
}

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
    // https://mvnrepository.com/artifact/org.springframework.boot/spring-boot-starter-web
    implementation("org.springframework.boot:spring-boot-starter-web:3.1.5")

    implementation("com.google.code.gson:gson:2.10.1")
    testImplementation(platform("org.junit:junit-bom:5.9.1"))
    testImplementation("org.junit.jupiter:junit-jupiter")
}

tasks.test {
    useJUnitPlatform()
}

tasks {
    withType<ShadowJar> {
        mergeServiceFiles() // Merge Spring Boot service files
        append("META-INF/spring.handlers")
        append("META-INF/spring.schemas")
        append("META-INF/spring.tooling")
        transform(PropertiesFileTransformer::class.java) {
            paths = listOf("META-INF/spring.factories")
            mergeStrategy = "append"
        }
    }
}

tasks.withType<Jar> {
    manifest {
        attributes["Main-Class"] = "de.tum.cit.ase.Main"
    }
}
