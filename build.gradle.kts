plugins {
    id("java")
}

group = "ase.cit.tum.de"
version = "1.0-SNAPSHOT"

repositories {
    mavenCentral()
}

dependencies {
    testImplementation(platform("org.junit:junit-bom:5.9.1"))
    testImplementation("org.junit.jupiter:junit-jupiter")
    implementation("com.atlassian.bamboo:bamboo-specs:9.2.1")
}

tasks.test {
    useJUnitPlatform()
}